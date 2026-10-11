"""Reproducible ONNX evaluation, confidence/coverage and calibration analysis.

Reproduces the reported test metrics from the exported ONNX model and produces
the evidence needed for a deployment-readiness decision:

  * per-image predictions (true class, predicted class, top-1 confidence,
    full probability vector) for each requested split
  * top-1 / top-5 accuracy per split
  * top-1 confidence distributions for correct vs incorrect predictions
  * full error matrix (true -> predicted) with counts
  * selective-prediction / rejection-threshold sweep: coverage, accepted
    accuracy, accepted errors and rejected counts at each candidate threshold
  * reliability (calibration) table, Expected/Max Calibration Error, Brier score

Two preprocessing modes are supported so the deployed backend path can be
compared against the path the metrics were measured with:

  --preprocess ultralytics  Resize(shortest edge, BILINEAR) -> CenterCrop -> /255
                            (what Ultralytics classify validation uses; this is
                            what metrics.json reports)
  --preprocess backend      the SHIPPED backend transform, imported verbatim from
                            backend/app/services/inference/preprocess.py
                            (shortest-edge BILINEAR resize -> centre crop -> /255),
                            so this mode exercises exactly what production runs

Requires the ML virtualenv (onnxruntime, numpy, Pillow, torchvision).
Read-only with respect to the dataset.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Evaluate exported ONNX classifier.")
    ap.add_argument("--onnx", required=True, help="Path to the .onnx model")
    ap.add_argument("--class-map", required=True, help="CLASS_INDEX_MAP JSON (index -> class)")
    ap.add_argument("--data", required=True, help="Dataset root containing train/ val/ test/")
    ap.add_argument("--splits", nargs="+", default=["test"], choices=["train", "val", "test"])
    ap.add_argument("--preprocess", default="ultralytics", choices=["ultralytics", "backend"])
    ap.add_argument("--thresholds", default="0.20,0.30,0.35,0.40,0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95",
                    help="Comma-separated confidence thresholds for the coverage sweep")
    ap.add_argument("--out", required=True, help="Output directory (usually the run directory)")
    ap.add_argument("--limit", type=int, default=0, help="Optional cap per class (0 = all)")
    return ap.parse_args(argv)


def load_names(path: Path) -> dict[int, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {int(k): str(v) for k, v in (raw.items() if isinstance(raw, dict) else enumerate(raw))}


def load_backend_preprocess():
    """Import the backend's reference-matching preprocess module directly.

    This makes the evaluator exercise the EXACT transform the backend ships, so
    backend inference and evaluation cannot drift. The module is dependency
    light (Pillow + numpy) and is loaded by path to avoid importing the backend
    package (and its FastAPI deps) into the ML virtualenv.
    """
    import importlib.util

    repo_root = Path(__file__).resolve().parent.parent
    module_path = repo_root / "backend" / "app" / "services" / "inference" / "preprocess.py"
    if not module_path.is_file():
        raise SystemExit(f"ERROR: backend preprocess module not found: {module_path}")
    spec = importlib.util.spec_from_file_location("loopwise_backend_preprocess", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.preprocess_image


def build_transform(mode: str, size: int):
    """Return a callable (PIL.Image -> NCHW float32 batch [1,3,size,size])."""
    if mode == "ultralytics":
        from torchvision import transforms as T

        tv = T.Compose([
            T.Resize(size, interpolation=T.InterpolationMode.BILINEAR),
            T.CenterCrop(size),
            T.ToTensor(),
        ])

        def _ultralytics(img):
            return tv(img.convert("RGB")).numpy()[np.newaxis, ...]

        return _ultralytics

    # backend: use the shipped backend transform verbatim
    return load_backend_preprocess()


def preprocess(path: Path, mode: str, size: int, transform) -> np.ndarray:
    from PIL import Image

    img = Image.open(path)
    if mode == "ultralytics":
        return transform(img)
    return transform(img, size)  # backend preprocess_image(img, size)


def evaluate_split(sess, input_name: str, names: dict[int, str], data_root: Path,
                   split: str, mode: str, transform, size: int, limit: int) -> tuple[list[dict], str]:
    split_dir = data_root / split
    classes = [names[i] for i in sorted(names)]
    rows: list[dict] = []
    output_mode = "unknown"
    for idx, cls in enumerate(classes):
        cdir = split_dir / cls
        if not cdir.is_dir():
            print(f"WARN: missing {cdir}", file=sys.stderr)
            continue
        files = sorted(p for p in cdir.iterdir()
                       if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
        if limit:
            files = files[:limit]
        for p in files:
            x = preprocess(p, mode, size, transform)
            out = sess.run(None, {input_name: x})[0][0]
            probs, detected = _probs(out)
            if output_mode == "unknown":
                output_mode = detected
            elif detected != output_mode:
                print(f"WARN: mixed model output types ({detected} vs {output_mode})",
                      file=sys.stderr)
            order = np.argsort(-probs)
            top1 = int(order[0])
            top5 = [int(i) for i in order[:5]]
            rows.append({
                "file": f"{split}/{cls}/{p.name}",
                "true_index": idx,
                "true_class": cls,
                "pred_index": top1,
                "pred_class": names[top1],
                "confidence": float(probs[top1]),
                "prob_true_class": float(probs[idx]),
                "top5_indices": top5,
                "top5_classes": [names[i] for i in top5],
                "top5_confidences": [float(probs[i]) for i in order[:5]],
                "prob_vector": [float(v) for v in probs],
                "correct": bool(top1 == idx),
                "in_top5": bool(idx in top5),
            })
        print(f"  [{split}/{mode}] {cls}: {len(files)}", file=sys.stderr)
    return rows, output_mode


def _probs(raw: np.ndarray) -> tuple[np.ndarray, str]:
    """Return (probabilities, mode).

    Ultralytics YOLO26-cls ONNX exports emit ALREADY-SOFTMAXED probabilities
    (sum == 1, all entries in [0, 1]). Applying softmax again compresses every
    confidence toward 1/n_classes and destroys thresholding and calibration.
    Detect this instead of assuming logits.
    """
    x = np.asarray(raw, dtype=np.float64).ravel()
    if x.min() >= 0.0 and abs(float(x.sum()) - 1.0) < 1e-3:
        return x / x.sum(), "already_probabilities"
    m = x.max()
    e = np.exp(x - m)
    return e / e.sum(), "logits_softmaxed"


def _stats(v: np.ndarray) -> dict:
    if v.size == 0:
        return {"n": 0}
    return {
        "n": int(v.size),
        "mean": float(v.mean()),
        "std": float(v.std()),
        "min": float(v.min()),
        "p10": float(np.percentile(v, 10)),
        "p25": float(np.percentile(v, 25)),
        "median": float(np.percentile(v, 50)),
        "p75": float(np.percentile(v, 75)),
        "p90": float(np.percentile(v, 90)),
        "max": float(v.max()),
    }


def analyze(rows: list[dict], thresholds: list[float], classes: list[str]) -> dict:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    conf = np.array([r["confidence"] for r in rows], dtype=np.float64)
    correct = np.array([r["correct"] for r in rows], dtype=bool)
    in_top5 = np.array([r["in_top5"] for r in rows], dtype=bool)

    out: dict = {
        "n": n,
        "top1_accuracy": float(correct.mean()),
        "top5_accuracy": float(in_top5.mean()),
        "confidence_all": _stats(conf),
        "confidence_correct": _stats(conf[correct]),
        "confidence_incorrect": _stats(conf[~correct]),
    }

    # error matrix true -> predicted
    ci = {c: i for i, c in enumerate(classes)}
    cm = np.zeros((len(classes), len(classes)), dtype=np.int64)
    for r in rows:
        cm[ci[r["true_class"]], ci[r["pred_class"]]] += 1
    out["error_matrix"] = {
        "classes": classes,
        "matrix": [[int(v) for v in row] for row in cm],
        "per_class": [
            {
                "class": classes[i],
                "n": int(cm[i].sum()),
                "correct": int(cm[i, i]),
                "accuracy": float(cm[i, i] / cm[i].sum()) if cm[i].sum() else None,
                "top_confusions": sorted(
                    ({"predicted": classes[j], "count": int(cm[i, j])}
                     for j in range(len(classes)) if i != j and cm[i, j] > 0),
                    key=lambda d: -d["count"])[:5],
            }
            for i in range(len(classes))
        ],
    }

    # selective prediction / rejection-threshold sweep
    sweep = []
    for t in thresholds:
        accepted = conf >= t
        acc_n = int(accepted.sum())
        acc_correct = int((accepted & correct).sum())
        acc_wrong = acc_n - acc_correct
        rej_n = int((~accepted).sum())
        rej_correct = int(((~accepted) & correct).sum())
        rej_wrong = rej_n - rej_correct
        sweep.append({
            "threshold": t,
            "accepted": acc_n,
            "coverage": acc_n / n,
            "rejected": rej_n,
            "accepted_correct": acc_correct,
            "accepted_incorrect": acc_wrong,
            "rejected_correct": rej_correct,
            "rejected_incorrect": rej_wrong,
            "accuracy_accepted": (acc_correct / acc_n) if acc_n else None,
            "error_rate_accepted": (acc_wrong / acc_n) if acc_n else None,
            # fraction of ALL errors that this threshold would have caught
            "error_catch_rate": (rej_wrong / int((~correct).sum())) if (~correct).sum() else None,
        })
    out["threshold_sweep"] = sweep

    # reliability / calibration
    bins = np.linspace(0.0, 1.0, 11)
    rel = []
    ece = 0.0
    for i in range(10):
        lo, hi = bins[i], bins[i + 1]
        mask = (conf >= lo) & (conf < hi if i < 9 else conf <= hi)
        c = int(mask.sum())
        if c == 0:
            rel.append({"bin": [float(lo), float(hi)], "n": 0})
            continue
        avg_conf = float(conf[mask].mean())
        acc = float(correct[mask].mean())
        ece += (c / n) * abs(acc - avg_conf)
        rel.append({
            "bin": [float(lo), float(hi)],
            "n": c,
            "avg_confidence": avg_conf,
            "empirical_accuracy": acc,
            "gap": acc - avg_conf,
        })
    out["calibration"] = {
        "bins": rel,
        "ece": float(ece),
    }
    return out


def analyze_full_probs(rows: list[dict], classes: list[str]) -> float:
    """Multiclass Brier score from the full probability vector."""
    brier = 0.0
    for r in rows:
        p = np.asarray(r["prob_vector"], dtype=np.float64)
        y = np.zeros(len(classes))
        y[r["true_index"]] = 1.0
        brier += float(np.sum((p - y) ** 2))
    return brier / len(rows) if rows else float("nan")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    import onnxruntime as ort

    onnx_path = Path(args.onnx)
    if not onnx_path.is_file():
        print(f"ERROR: ONNX not found: {onnx_path}", file=sys.stderr)
        return 2
    names = load_names(Path(args.class_map))
    classes = [names[i] for i in sorted(names)]
    data_root = Path(args.data)
    size = 224
    thresholds = [float(x) for x in args.thresholds.split(",")]

    sess = ort.InferenceSession(str(onnx_path))
    inp = sess.get_inputs()[0]
    input_name = inp.name
    print(f"model input: {inp.name} {inp.shape}", file=sys.stderr)
    print(f"classes ({len(classes)}): {classes}", file=sys.stderr)

    transform = build_transform(args.preprocess, size)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "model": str(onnx_path.resolve()),
        "class_map": str(Path(args.class_map).resolve()),
        "classes": classes,
        "preprocess": args.preprocess,
        "input_shape": [str(d) for d in (inp.shape or [])],
        "splits": {},
    }

    all_rows_by_split: dict[str, list[dict]] = {}
    for split in args.splits:
        print(f"\n=== {split} ({args.preprocess}) ===", file=sys.stderr)
        rows, output_mode = evaluate_split(sess, input_name, names, data_root, split,
                                           args.preprocess, transform, size, args.limit)
        all_rows_by_split[split] = rows
        a = analyze(rows, thresholds, classes)
        a["brier_score"] = analyze_full_probs(rows, classes)
        a["model_output_type"] = output_mode
        report["splits"][split] = a
        print(f"  model_output_type={output_mode}")
        print(f"  images={a['n']} top1={a['top1_accuracy']:.4f} top5={a['top5_accuracy']:.4f} "
              f"conf_mean={a['confidence_all']['mean']:.4f} "
              f"ece={a['calibration']['ece']:.4f} brier={a['brier_score']:.4f}")

    # persist per-image predictions (includes the full 8-way probability vector
    # so downstream analyses, e.g. simulating a different softmax convention,
    # can be recomputed without re-running inference)
    for split, rows in all_rows_by_split.items():
        (out_dir / f"predictions_{split}_{args.preprocess}.json").write_text(
            json.dumps(rows, indent=1), encoding="utf-8")

    (out_dir / f"analysis_{args.preprocess}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_dir}/analysis_{args.preprocess}.json and per-split predictions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

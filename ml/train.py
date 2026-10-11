"""Reproducible YOLO26 classification training for LoopWise (ML env only).

- Task: image CLASSIFICATION (`yolo classify`), matching the API contract
  (one predicted_class + top3 per photo). No bounding boxes required.
- Base weights: official Ultralytics YOLO26 pretrained checkpoint
  (default `yolo26n-cls.pt`, auto-downloaded by Ultralytics on first run).
- Reproducibility: fixed --seed, deterministic=True, runs logged with all
  hyperparameters to ml/runs/<name>/settings_used.json.
- Evaluation: validates on val/ every epoch, then reports test/ metrics
  (top-1/top-5 + per-class) via `model.val(split='test')`.
- This script NEVER runs without a validated dataset: it calls
  ml/validate_dataset.py first and aborts (exit 2) if validation fails.

Requires the ML virtualenv (ml/requirements-ml.txt). Do NOT run in backend/.venv.

  ml/.venv/Scripts/python ml/train.py --data ml/data/waste-classify --epochs 50
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train YOLO26 classifier (reproducible).")
    ap.add_argument("--data", required=True, help="Dataset root (train/ val/ test/ class folders)")
    ap.add_argument("--model", default="yolo26n-cls.pt", help="Pretrained checkpoint (default: %(default)s)")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=224, help="YOLO-cls default resolution")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--patience", type=int, default=15, help="Early-stopping patience (epochs)")
    ap.add_argument("--device", default="cpu", help="'cpu' or CUDA id, e.g. '0'")
    ap.add_argument("--project", default="ml/runs", help="Runs directory")
    ap.add_argument("--name", default="baseline", help="Run name (timestamped automatically)")
    ap.add_argument("--no-test-eval", action="store_true", help="Skip final test/ evaluation")
    ap.add_argument("--model-version", default="yolo26n-cls-v1",
                    help="MODEL_VERSION label recorded in run_record.json and used by the backend")
    return ap.parse_args(argv)


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _package_versions() -> dict[str, str]:
    import importlib.metadata as md

    out = {"python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"}
    for name in ("torch", "torchvision", "ultralytics", "numpy", "Pillow", "onnx",
                 "onnxruntime", "PyYAML", "opencv-python"):
        try:
            out[name] = md.version(name)
        except md.PackageNotFoundError:
            out[name] = "not-installed"
    return out


def _git_commit(repo_root: Path) -> str | None:
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root,
                              capture_output=True, text=True, timeout=15)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except Exception:
        return None


def _split_counts(data: Path) -> dict[str, dict[str, int]]:
    exts = (".jpg", ".jpeg", ".png", ".webp")
    counts: dict[str, dict[str, int]] = {}
    for split in ("train", "val", "test"):
        sdir = data / split
        per: dict[str, int] = {}
        if sdir.is_dir():
            for cls_dir in sorted(p for p in sdir.iterdir() if p.is_dir()):
                per[cls_dir.name] = sum(1 for f in cls_dir.iterdir()
                                        if f.suffix.lower() in exts)
        counts[split] = per
    return counts


def build_run_record(args: argparse.Namespace, data: Path, repo_root: Path,
                     canonical_list: list[str], run_name: str) -> dict:
    """Everything needed to reproduce or audit this run (requirements: log,
    package versions, dataset summary, class mapping, checkpoint provenance,
    model version)."""
    mapping_path = repo_root / "ml" / "source_mapping.json"
    mapping = (json.loads(mapping_path.read_text(encoding="utf-8"))
               if mapping_path.is_file() else {})
    base = Path(args.model)
    provenance: dict = {
        "base_checkpoint": args.model,
        "architecture": "yolo26n-cls (Ultralytics YOLO26 classification, ImageNet-1k pretrained)",
        "pretrained_on": "ImageNet-1k",
        "framework": "ultralytics",
        "download_url": (f"https://github.com/ultralytics/assets/releases/download/"
                         f"v8.4.0/{base.name}"),
        "license": ("AGPL-3.0-or-later (Ultralytics). LoopWise itself is MIT: distributing "
                    "trained weights derived from these weights may require AGPL "
                    "compliance or an Ultralytics Enterprise license."),
        "transfer_learning": True,
        "trainable": True,
    }
    if base.is_file():
        provenance["local_path"] = str(base.resolve())
        provenance["size_bytes"] = base.stat().st_size
        provenance["sha256"] = _sha256_file(base)

    return {
        "model_version": args.model_version,
        "run_name": run_name,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(repo_root),
        "task": "classify",
        "classes_index_order": canonical_list,
        "num_classes": len(canonical_list),
        "dataset": {
            "path": str(data),
            "counts": _split_counts(data),
            "summary_json": str((data / "dataset_summary.json").resolve()),
            "manifest_csv": str((data / "manifest.csv").resolve()),
            "test_held_out": True,
        },
        "class_mapping": {
            "source_mapping_file": str(mapping_path.resolve()) if mapping_path.is_file() else None,
            "labels": mapping.get("labels", mapping),
            "source": mapping.get("source", {}),
        },
        "hyperparameters": args.__dict__,
        "provenance": provenance,
        "package_versions": _package_versions(),
        "hardware": {
            "torch_cuda_available": __import__("torch").cuda.is_available(),
            "device": args.device,
        },
    }


def run_validation(data: Path, repo_root: Path) -> None:
    cmd = [sys.executable, str(repo_root / "ml" / "validate_dataset.py"), "--data", str(data)]
    print(f"+ {' '.join(cmd)}")
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        print("ABORT: dataset validation failed — training will not start.", file=sys.stderr)
        sys.exit(2)


def build_data_yaml(data: Path, repo_root: Path, out_yaml: Path) -> Path:
    """Write a REPRODUCIBILITY RECORD of the dataset path + canonical class
    order from ml/classes.json.

    NOTE: Ultralytics image CLASSIFICATION does NOT accept a data.yaml — it
    requires the dataset *directory* (`data=<dir>`) and derives class indices
    from the train/ class folder names sorted alphabetically. We therefore pass
    `str(data)` to YOLO below and only keep this YAML as an audit record. The
    alphabetical-sort invariant is enforced by the guard in main()."""
    canonical = json.loads((repo_root / "ml" / "classes.json").read_text(encoding="utf-8"))
    lines = [
        "# Generated by ml/train.py — do not edit (re-run train.py instead).",
        f"path: {str(data).replace(chr(92), '/')}",
        "train: train",
        "val: val",
        "test: test",
        "names:",
    ]
    for i in sorted(canonical, key=int):
        lines.append(f"  {i}: {canonical[i]}")
    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    out_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_yaml


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    data = Path(args.data)
    if not data.is_absolute():
        data = (Path.cwd() / args.data).resolve()

    run_validation(data, repo_root)

    canonical = json.loads((repo_root / "ml" / "classes.json").read_text(encoding="utf-8"))
    canonical_list = [canonical[str(i)] for i in range(len(canonical))]
    if canonical_list != sorted(canonical_list):
        print("ERROR: ml/classes.json is not in alphabetical order. Ultralytics "
              "classification derives class indices from class folder names sorted "
              "alphabetically, so a non-alphabetical order would mislabel every "
              "prediction and mismatch the exported CLASS_INDEX_MAP. Reorder "
              "ml/classes.json (and re-prepare the dataset) before training.",
              file=sys.stderr)
        return 2
    for split in ("train", "val"):
        sdir = data / split
        found = sorted(p.name for p in sdir.iterdir() if p.is_dir()) if sdir.is_dir() else []
        if found and found != canonical_list:
            print(f"ERROR: '{split}' class folders {found} do not match the canonical "
                  f"alphabetical order {canonical_list}. Re-run ml/prepare_dataset.py.",
                  file=sys.stderr)
            return 2

    from ultralytics import YOLO  # ML env only; lazy so --help works anywhere

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_name = f"{args.name}-{stamp}"
    # Ultralytics nests a RELATIVE project under <runs_dir>/<task>/ (e.g.
    # runs/classify/<project>/<name>), so our own run_dir guess would be wrong.
    # Resolve to an absolute path so the run lands exactly where we expect.
    project = Path(args.project)
    if not project.is_absolute():
        project = (Path.cwd() / args.project).resolve()
    project.mkdir(parents=True, exist_ok=True)
    data_yaml = build_data_yaml(data, repo_root, project / f"data-used-{run_name}.yaml")
    settings = {
        "task": "classify",
        "model": args.model,
        "data": str(data),
        "data_yaml": str(data_yaml),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "seed": args.seed,
        "patience": args.patience,
        "device": args.device,
        "deterministic": True,
        "single_cls": False,
        "pretrained": True,
        "classes_order": json.loads((repo_root / "ml" / "classes.json").read_text()),
    }

    print(f"Loading pretrained weights: {args.model}")
    model = YOLO(args.model)
    results = model.train(
        data=str(data),  # Ultralytics classify wants the directory, not data.yaml
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        seed=args.seed,
        deterministic=True,
        patience=args.patience,
        device=args.device,
        project=str(project),
        name=run_name,
        exist_ok=False,
        verbose=True,
    )
    # Prefer the directory Ultralytics actually wrote to (self-healing if the
    # nesting rules ever change).
    actual = getattr(getattr(model, "trainer", None), "save_dir", None)
    run_dir = Path(actual) if actual else (project / run_name)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "settings_used.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")

    record = build_run_record(args, data, repo_root, canonical_list, run_name)
    record["run_dir"] = str(run_dir.resolve())
    (run_dir / "run_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Run record: {run_dir / 'run_record.json'}")

    metrics = {"val_top1": float(getattr(results, "top1", float("nan"))),
               "val_top5": float(getattr(results, "top5", float("nan")))}
    print(f"VAL top1={metrics['val_top1']:.4f} top5={metrics['val_top5']:.4f}")

    if not args.no_test_eval and (data / "test").is_dir():
        test_metrics = model.val(data=str(data), split="test")
        metrics["test_top1"] = float(getattr(test_metrics, "top1", float("nan")))
        metrics["test_top5"] = float(getattr(test_metrics, "top5", float("nan")))
        print(f"TEST top1={metrics['test_top1']:.4f} top5={metrics['test_top5']:.4f}")
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    best_pt = run_dir / "weights" / "best.pt"
    print(f"\nDone. Best checkpoint: {best_pt}")
    print("Next (after approval):")
    print(f"  ml/.venv/Scripts/python ml/export_onnx.py --weights {best_pt} --out ml/models/loopwise-yolo26n-cls.onnx")
    return 0


if __name__ == "__main__":
    sys.exit(main())

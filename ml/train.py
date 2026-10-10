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
    return ap.parse_args(argv)


def run_validation(data: Path, repo_root: Path) -> None:
    cmd = [sys.executable, str(repo_root / "ml" / "validate_dataset.py"), "--data", str(data)]
    print(f"+ {' '.join(cmd)}")
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        print("ABORT: dataset validation failed — training will not start.", file=sys.stderr)
        sys.exit(2)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    data = Path(args.data)
    if not data.is_absolute():
        data = (Path.cwd() / args.data).resolve()

    run_validation(data, repo_root)

    from ultralytics import YOLO  # ML env only; lazy so --help works anywhere

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_name = f"{args.name}-{stamp}"
    settings = {
        "task": "classify",
        "model": args.model,
        "data": str(data),
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
        data=str(data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        seed=args.seed,
        deterministic=True,
        patience=args.patience,
        device=args.device,
        project=args.project,
        name=run_name,
        exist_ok=False,
        verbose=True,
    )
    run_dir = Path(args.project) / run_name
    (run_dir / "settings_used.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")

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

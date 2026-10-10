"""Validate the LoopWise waste-classification dataset (stdlib only).

Checks, without any ML dependency:
  - dataset root exists with train/ val/ (test/ optional but required for final eval)
  - every split contains exactly the canonical classes from ml/classes.json
  - files are JPEG/PNG/WebP, non-empty, with per-class counts and balance report
  - deterministic train/val/test separation (no filename appears in 2 splits)

Exit codes: 0 = ready for training, 1 = usage error, 2 = dataset missing/invalid.

Example:
  python ml/validate_dataset.py --data ml/data/waste-classify
  python ml/validate_dataset.py --data ml/data/waste-classify --auto-split 0.15
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
from pathlib import Path

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_TRAIN_PER_CLASS = 100   # ERROR below 20, WARN below this
MIN_VAL_PER_CLASS = 20
MIN_TEST_PER_CLASS = 20
HARD_MIN_PER_CLASS = 20


def load_canonical(repo_root: Path) -> list[str]:
    with open(repo_root / "ml" / "classes.json", encoding="utf-8") as f:
        raw = json.load(f)
    return [raw[str(i)] for i in range(len(raw))]


def list_images(class_dir: Path) -> list[Path]:
    if not class_dir.is_dir():
        return []
    return sorted(
        p for p in class_dir.iterdir()
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTS and p.stat().st_size > 0
    )


def validate(data_root: Path, canonical: list[str]) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    counts: dict[str, dict[str, int]] = {}

    if not data_root.is_dir():
        errors.append(
            f"Dataset root not found: {data_root}\n"
            "  REQUIRED layout (classification folders, no bounding boxes):\n"
            "    <root>/train/<material_id>/*.jpg  (8 classes, see ml/classes.json)\n"
            "    <root>/val/<material_id>/*.jpg\n"
            "    <root>/test/<material_id>/*.jpg\n"
            "  Accepted formats: JPEG, PNG, WebP. At least "
            f"{HARD_MIN_PER_CLASS} non-empty images per class in train/."
        )
        return errors, warnings, counts

    for split in ("train", "val", "test"):
        split_dir = data_root / split
        counts[split] = {}
        if not split_dir.is_dir():
            msg = f"Missing split directory: {split_dir}"
            (errors if split in ("train", "val") else warnings).append(
                msg + (" (test/ is required before final evaluation)" if split == "test" else "")
            )
            continue
        found = sorted(p.name for p in split_dir.iterdir() if p.is_dir())
        for missing in [c for c in canonical if c not in found]:
            errors.append(f"[{split}] missing class directory: {missing}/")
        for extra in [c for c in found if c not in canonical]:
            warnings.append(f"[{split}] unexpected directory '{extra}/' (not in ml/classes.json; ignored by training)")
        for cls in canonical:
            n = len(list_images(split_dir / cls))
            counts[split][cls] = n

    # Count thresholds.
    for cls in canonical:
        ntr = counts.get("train", {}).get(cls, 0)
        if ntr < HARD_MIN_PER_CLASS:
            errors.append(f"[train] class '{cls}' has {ntr} images (< hard minimum {HARD_MIN_PER_CLASS})")
        elif ntr < MIN_TRAIN_PER_CLASS:
            warnings.append(f"[train] class '{cls}' has {ntr} images (< recommended {MIN_TRAIN_PER_CLASS})")
    for split, minimum in (("val", MIN_VAL_PER_CLASS), ("test", MIN_TEST_PER_CLASS)):
        if split not in counts or not counts[split]:
            continue  # missing dir already reported above
        for cls in canonical:
            n = counts[split].get(cls, 0)
            if n < HARD_MIN_PER_CLASS:
                errors.append(f"[{split}] class '{cls}' has {n} images (< hard minimum {HARD_MIN_PER_CLASS})")
            elif n < minimum:
                warnings.append(f"[{split}] class '{cls}' has {n} images (< recommended {minimum})")

    # Leakage: same filename in more than one split for the same class.
    for cls in canonical:
        seen: dict[str, str] = {}
        for split in ("train", "val", "test"):
            for p in list_images(data_root / split / cls):
                if p.name in seen:
                    errors.append(
                        f"Leakage: '{p.name}' (class {cls}) present in both "
                        f"{seen[p.name]}/ and {split}/ — splits must be disjoint"
                    )
                else:
                    seen[p.name] = split

    # Balance report (informational).
    if counts.get("train"):
        vals = [counts["train"].get(c, 0) for c in canonical]
        if vals and max(vals) > 0 and min(vals) / max(vals) < 0.5:
            warnings.append(
                f"[train] class imbalance: smallest class {min(vals)} vs largest {max(vals)} "
                "(ratio < 0.5; consider collecting more of the minority class)"
            )
    return errors, warnings, counts


def auto_split(data_root: Path, canonical: list[str], val_frac: float, seed: int) -> None:
    """Deterministically move val_frac of each train/ class into val/ (and test/)."""
    rng = random.Random(seed)
    for cls in canonical:
        src = data_root / "train" / cls
        files = list_images(src)
        if not files:
            continue
        rng.shuffle(files)
        n_val = max(1, int(len(files) * val_frac))
        for dest_name, chunk in (("val", files[:n_val]),):
            dest = data_root / dest_name / cls
            dest.mkdir(parents=True, exist_ok=True)
            for p in chunk:
                shutil.move(str(p), str(dest / p.name))
    print(f"auto-split: moved ~{val_frac * 100:.0f}% of train/ into val/ (seed={seed})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate LoopWise waste dataset (no ML deps).")
    ap.add_argument("--data", required=True, help="Dataset root directory")
    ap.add_argument("--auto-split", type=float, default=0.0, metavar="FRAC",
                    help="If val/ missing, create it by moving FRAC of train/ (deterministic, --seed)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    canonical = load_canonical(repo_root)
    data_root = Path(args.data)
    if not data_root.is_absolute():
        data_root = (Path.cwd() / data_root).resolve()

    if args.auto_split > 0 and not (data_root / "val").is_dir() and (data_root / "train").is_dir():
        auto_split(data_root, canonical, args.auto_split, args.seed)

    errors, warnings, counts = validate(data_root, canonical)

    print(f"Dataset root : {data_root}")
    print(f"Classes      : {len(canonical)} {canonical}")
    for split in ("train", "val", "test"):
        if split in counts and counts[split]:
            total = sum(counts[split].values())
            detail = ", ".join(f"{c}={counts[split].get(c, 0)}" for c in canonical)
            print(f"[{split}] total={total} | {detail}")
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print(f"\nVALIDATION FAILED ({len(errors)} error(s)). See dataset requirements in ml/README.md.")
        return 2
    print("\nVALIDATION PASSED — dataset is ready for ml/train.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

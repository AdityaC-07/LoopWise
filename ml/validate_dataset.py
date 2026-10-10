"""Validate the LoopWise waste-classification dataset (stdlib only).

Checks, without any ML dependency:
  - dataset root exists with train/ val/ (test/ optional but required for final eval)
  - every split contains exactly the canonical classes from ml/classes.json
  - ml/classes.json and ml/data.yaml name lists agree (index-identical)
  - files are JPEG/PNG/WebP by signature, non-empty, with per-class counts
  - deterministic train/val/test separation (no filename in two splits)
  - no duplicate image BYTES across splits (sha256 leakage check, --no-hash to skip)
  - optional JSON summary via --json PATH (machine-readable report)

Exit codes: 0 = ready for training, 1 = usage error, 2 = dataset missing/invalid.

Example:
  python ml/validate_dataset.py --data ml/data/waste-classify
  python ml/validate_dataset.py --data ml/data/waste-classify --auto-split 0.15
  python ml/validate_dataset.py --data ml/data/waste-classify --json report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import sys
from datetime import datetime, timezone
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


def load_data_yaml_names(repo_root: Path) -> list[str] | None:
    """Parse the `names:` block of ml/data.yaml without a YAML dependency.

    Returns names ordered by index, or None if the file/section is missing.
    """
    yaml_path = repo_root / "ml" / "data.yaml"
    if not yaml_path.is_file():
        return None
    names: dict[int, str] = {}
    in_names = False
    entry_re = re.compile(r"^\s+(\d+):\s*([A-Za-z0-9_\-]+)\s*$")
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0].rstrip()
        if not stripped:
            continue
        if stripped.startswith("names:"):
            in_names = True
            continue
        if in_names:
            m = entry_re.match(stripped)
            if m:
                names[int(m.group(1))] = m.group(2)
            elif not line[0].isspace():
                in_names = False
    if not names:
        return None
    return [names[i] for i in sorted(names)]


def check_consistency(canonical: list[str], yaml_names: list[str] | None) -> list[str]:
    """classes.json and data.yaml must define the same classes in the same order."""
    if yaml_names is None:
        return ["ml/data.yaml has no readable `names:` section"]
    if yaml_names != canonical:
        return [
            "ml/classes.json and ml/data.yaml disagree on the class list/order.\n"
            f"  classes.json : {canonical}\n"
            f"  data.yaml    : {yaml_names}\n"
            "  Update BOTH files together, then re-export CLASS_INDEX_MAP and bump MODEL_VERSION."
        ]
    return []


def list_images(class_dir: Path) -> list[Path]:
    if not class_dir.is_dir():
        return []
    return sorted(
        p for p in class_dir.iterdir()
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTS and p.stat().st_size > 0
    )


def magic_ok(path: Path) -> bool:
    """True if the file starts with a recognised JPEG/PNG/WebP signature."""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError:
        return False
    if head.startswith(b"\xff\xd8\xff"):
        return True
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return True
    return False


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(data_root: Path, canonical: list[str], check_hashes: bool = True
             ) -> tuple[list[str], list[str], dict, int]:
    errors: list[str] = []
    warnings: list[str] = []
    counts: dict[str, dict[str, int]] = {}
    files_checked = 0

    if not data_root.is_dir():
        errors.append(
            f"Dataset root not found: {data_root}\n"
            "  REQUIRED layout (classification folders, no bounding boxes):\n"
            "    <root>/train/<class>/*.jpg  (8 classes, see ml/classes.json)\n"
            "    <root>/val/<class>/*.jpg\n"
            "    <root>/test/<class>/*.jpg\n"
            "  Accepted formats: JPEG, PNG, WebP. At least "
            f"{HARD_MIN_PER_CLASS} non-empty images per class in train/.\n"
            "  Build one with: python ml/prepare_dataset.py --source-root <raw> --out <root>"
        )
        return errors, warnings, counts, files_checked

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
            files = list_images(split_dir / cls)
            counts[split][cls] = len(files)
            for p in files:
                files_checked += 1
                if not magic_ok(p):
                    errors.append(f"[{split}] not a valid JPEG/PNG/WebP file (bad signature): {p.relative_to(data_root)}")

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

    # Leakage A: same filename in more than one split for the same class.
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

    # Leakage B: identical image BYTES across different splits (renamed copies).
    if check_hashes:
        by_hash: dict[str, list[tuple[str, str, Path]]] = {}
        for split in ("train", "val", "test"):
            for cls in canonical:
                for p in list_images(data_root / split / cls):
                    by_hash.setdefault(sha256_file(p), []).append((split, cls, p))
        for digest, locs in by_hash.items():
            splits = {s for s, _, _ in locs}
            if len(splits) > 1:
                places = ", ".join(f"{s}/{c}/{p.name}" for s, c, p in locs)
                errors.append(
                    f"Leakage: identical image bytes (sha256 {digest[:12]}…) in multiple splits: {places}"
                )
            else:
                classes = {c for _, c, _ in locs}
                if len(classes) > 1:
                    places = ", ".join(f"{s}/{c}/{p.name}" for s, c, p in locs)
                    warnings.append(
                        f"Identical bytes in the same split across classes (possible mislabel): {places}"
                    )

    # Balance report (informational).
    if counts.get("train"):
        vals = [counts["train"].get(c, 0) for c in canonical]
        if vals and max(vals) > 0 and min(vals) / max(vals) < 0.5:
            warnings.append(
                f"[train] class imbalance: smallest class {min(vals)} vs largest {max(vals)} "
                "(ratio < 0.5; consider --max-per-class when preparing, or collect more minority data)"
            )
    return errors, warnings, counts, files_checked


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
    ap.add_argument("--no-hash", action="store_true",
                    help="Skip the sha256 cross-split leakage check (faster on huge datasets)")
    ap.add_argument("--json", metavar="PATH", default=None,
                    help="Write a machine-readable validation summary to PATH")
    args = ap.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    canonical = load_canonical(repo_root)
    yaml_names = load_data_yaml_names(repo_root)
    data_root = Path(args.data)
    if not data_root.is_absolute():
        data_root = (Path.cwd() / data_root).resolve()

    if args.auto_split > 0 and not (data_root / "val").is_dir() and (data_root / "train").is_dir():
        auto_split(data_root, canonical, args.auto_split, args.seed)

    consistency_errors = check_consistency(canonical, yaml_names)
    errors, warnings, counts, files_checked = validate(
        data_root, canonical, check_hashes=not args.no_hash)
    errors = consistency_errors + errors

    print(f"Dataset root : {data_root}")
    print(f"Classes      : {len(canonical)} {canonical}")
    print(f"Class map    : ml/classes.json == ml/data.yaml -> {'OK' if not consistency_errors else 'MISMATCH'}")
    for split in ("train", "val", "test"):
        if split in counts and counts[split]:
            total = sum(counts[split].values())
            detail = ", ".join(f"{c}={counts[split].get(c, 0)}" for c in canonical)
            print(f"[{split}] total={total} | {detail}")
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if args.json:
        report = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dataset_root": str(data_root),
            "classes": canonical,
            "data_yaml_names": yaml_names,
            "counts": counts,
            "files_checked": files_checked,
            "hash_check": not args.no_hash,
            "errors": errors,
            "warnings": warnings,
            "passed": not errors,
        }
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote JSON summary: {args.json}")

    if errors:
        print(f"\nVALIDATION FAILED ({len(errors)} error(s)). See dataset requirements in ml/README.md.")
        return 2
    print("\nVALIDATION PASSED — dataset is ready for ml/train.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

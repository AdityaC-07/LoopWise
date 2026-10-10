"""Prepare the LoopWise training dataset from a raw folder-per-class source.

Reads raw images organised in one folder per SOURCE label (e.g. the Kaggle
"Garbage Classification (12 classes)" dataset), maps every source label to
one canonical broad class from ml/classes.json, removes duplicate images,
assigns deterministic train/val/test splits, strips EXIF metadata, and
writes a training-ready dataset:

  <out>/train/<class>/*.jpg   <out>/val/<class>/*.jpg   <out>/test/<class>/*.jpg
  <out>/manifest.csv            every kept image (hash, split, provenance)
  <out>/excluded_images.csv     every rejected image + reason
  <out>/dataset_summary.json    counts, config, warnings
  <out>/data.yaml               generated dataset config (absolute path)
  <out>/README.md               provenance + how this dataset was built

Guarantees:
  - The raw source is NEVER modified (copy only; nothing is moved/deleted).
  - Deterministic: same source + same args => identical manifest.csv and
    identical splits (sha256 ordering + per-class seeded shuffle).
  - No label inference: every output class comes from ml/source_mapping.json;
    unmapped source folders are excluded and reported, never guessed.
  - Stdlib-only. When Pillow is available it verifies decodability, strips
    EXIF metadata on copy, and drops perceptual near-duplicates within a
    class (identical 64-bit dHash). Without Pillow those steps are skipped
    and reported as warnings in dataset_summary.json.

Exit codes: 0 = dataset written (or dry-run OK), 1 = usage error,
2 = source/mapping/output error.

Examples:
  python ml/prepare_dataset.py --source-root ml/data/raw --out ml/data/waste-classify
  python ml/prepare_dataset.py --source-root ml/data/raw --out ml/data/waste-classify \
      --max-per-class 1000 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
GENERATED_FILES = ("manifest.csv", "excluded_images.csv", "dataset_summary.json", "data.yaml", "README.md")
GENERATED_DIRS = ("train", "val", "test")

try:  # optional: deeper validation, EXIF strip, perceptual dedupe
    from PIL import Image
    _HAVE_PIL = True
except Exception:  # pragma: no cover - depends on environment
    Image = None  # type: ignore
    _HAVE_PIL = False

MANIFEST_FIELDS = ["dataset", "source_relpath", "source_class", "final_class",
                   "split", "sha256", "dhash", "output_relpath", "bytes"]
EXCLUDED_FIELDS = ["dataset", "source_relpath", "source_class", "reason", "detail"]


# --------------------------------------------------------------------------- io

def load_canonical(repo_root: Path) -> list[str]:
    with open(repo_root / "ml" / "classes.json", encoding="utf-8") as f:
        raw = json.load(f)
    return [raw[str(i)] for i in range(len(raw))]


def load_mapping(mapping_file: Path, dataset_id: str) -> dict:
    if not mapping_file.is_file():
        raise FileNotFoundError(f"Mapping file not found: {mapping_file}")
    with open(mapping_file, encoding="utf-8") as f:
        all_maps = json.load(f)
    if dataset_id not in all_maps:
        known = ", ".join(sorted(all_maps)) or "(none)"
        raise ValueError(f"Unknown dataset '{dataset_id}' in {mapping_file}. Known: {known}")
    return all_maps[dataset_id]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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


def dhash_file(path: Path) -> str:
    """64-bit difference hash as 16 hex chars (Pillow only)."""
    im = Image.open(path).convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    data = im.tobytes()  # one byte per pixel, row-major (9 columns x 8 rows)
    bits = 0
    for row in range(8):
        base = row * 9
        for col in range(8):
            bits = (bits << 1) | (1 if data[base + col] > data[base + col + 1] else 0)
    return f"{bits:016x}"


def copy_image(src: Path, dst: Path, strip_exif: bool) -> None:
    """Copy src to dst, stripping EXIF/metadata when Pillow can re-save safely."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not (strip_exif and _HAVE_PIL):
        shutil.copy2(src, dst)
        return
    try:
        im = Image.open(src)
        fmt = (im.format or "").upper()
        if fmt == "JPEG":
            im.save(dst, format="JPEG", quality="keep")  # drops EXIF, keeps quant tables
        elif fmt == "PNG":
            im.save(dst, format="PNG")  # drops eXIf/text chunks unless explicitly passed
        else:  # WebP and unknown: plain copy (re-encode would degrade quality)
            shutil.copy2(src, dst)
        im.close()
    except Exception:
        shutil.copy2(src, dst)


# ------------------------------------------------------------------ discovery

def scan_source(source_root: Path, mapping: dict, dataset_id: str,
                canonical: list[str]) -> tuple[list[dict], list[dict], list[str]]:
    """Walk the raw source. Returns (records, excluded, warnings)."""
    label_map: dict[str, str] = mapping["map"]
    bad_labels = {s: t for s, t in label_map.items() if t not in canonical}
    if bad_labels:
        raise ValueError(
            f"Mapping targets not in ml/classes.json: {bad_labels}. "
            "Update ml/source_mapping.json and ml/classes.json together."
        )

    records: list[dict] = []
    excluded: list[dict] = []
    warnings: list[str] = []

    def drop(rel: str, src_label: str, reason: str, detail: str = "") -> None:
        excluded.append({"dataset": dataset_id, "source_relpath": rel,
                         "source_class": src_label, "reason": reason, "detail": detail})

    for p in sorted(source_root.iterdir()):
        if p.is_file():
            drop(p.name, "", "loose_file", "not inside a source class folder")
            continue
        src_label = p.name
        final_class = label_map.get(src_label)
        for f in sorted(p.iterdir()):
            rel = f"{src_label}/{f.name}"
            if not f.is_file():
                drop(rel, src_label, "not_a_file", "directory or special file")
                continue
            if final_class is None:
                drop(rel, src_label, "unmapped_source_label", "no mapping in source_mapping.json")
                continue
            if f.suffix.lower() not in ALLOWED_EXTS:
                drop(rel, src_label, "unsupported_extension", f.suffix or "(no extension)")
                continue
            if f.stat().st_size == 0:
                drop(rel, src_label, "empty_file", "0 bytes")
                continue
            if not magic_ok(f):
                drop(rel, src_label, "invalid_image_header", "unrecognised file signature")
                continue
            if _HAVE_PIL:
                try:
                    Image.open(f).verify()
                except Exception as e:
                    drop(rel, src_label, "undecodable_image", str(e)[:120])
                    continue
            records.append({
                "dataset": dataset_id,
                "path": f,
                "source_relpath": rel,
                "source_class": src_label,
                "final_class": final_class,
                "bytes": f.stat().st_size,
            })

    mapped_sources = {s for s in label_map if (source_root / s).is_dir()}
    missing_dirs = sorted(set(label_map) - mapped_sources)
    if missing_dirs:
        warnings.append(f"Source folders listed in mapping but absent: {', '.join(missing_dirs)}")
    present_targets = {label_map[s] for s in mapped_sources}
    for cls in canonical:
        if cls not in present_targets:
            warnings.append(f"Canonical class '{cls}' has no source folder — it will be absent from the dataset")
    if not records:
        raise ValueError(f"No usable images found under {source_root}")
    return records, excluded, warnings


# ------------------------------------------------------------------- dedupe

def dedupe(records: list[dict], excluded: list[dict], warnings: list[str],
           near_dup: bool = True) -> None:
    """Exact-hash then perceptual-hash dedupe, in place. Keeps first by sort order."""
    records.sort(key=lambda r: (r["source_relpath"]))

    seen_sha: dict[str, dict] = {}
    kept: list[dict] = []
    for r in records:
        r["sha256"] = sha256_file(r["path"])
        first = seen_sha.get(r["sha256"])
        if first is not None:
            excluded.append({"dataset": r["dataset"], "source_relpath": r["source_relpath"],
                             "source_class": r["source_class"], "reason": "duplicate_exact",
                             "detail": f"identical bytes to {first['source_relpath']}"})
            continue
        seen_sha[r["sha256"]] = r
        kept.append(r)
    records[:] = kept

    if not _HAVE_PIL:
        warnings.append("Pillow not available: skipped decodability check, EXIF stripping and perceptual dedupe")
        for r in records:
            r["dhash"] = ""
        return

    groups: dict[str, list[dict]] = {}
    for r in records:
        try:
            r["dhash"] = dhash_file(r["path"])
        except Exception:
            r["dhash"] = ""
            excluded.append({"dataset": r["dataset"], "source_relpath": r["source_relpath"],
                             "source_class": r["source_class"], "reason": "unreadable_for_dhash",
                             "detail": ""})
            continue
        if near_dup:
            groups.setdefault(f"{r['final_class']}|{r['dhash']}", []).append(r)
    if not near_dup:
        warnings.append("--no-near-dup: perceptual near-duplicates within a class were kept")

    drop_paths: set[str] = set()
    cross_class_collisions = 0
    for key, members in groups.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda r: r["source_relpath"])  # deterministic keeper
        for r in members[1:]:
            drop_paths.add(r["source_relpath"])
            excluded.append({"dataset": r["dataset"], "source_relpath": r["source_relpath"],
                             "source_class": r["source_class"], "reason": "duplicate_near",
                             "detail": f"same perceptual hash as {members[0]['source_relpath']}"})
    by_hash: dict[str, list[dict]] = {}
    for r in records:
        if r["dhash"]:
            by_hash.setdefault(r["dhash"], []).append(r)
    for members in by_hash.values():
        if len({r["final_class"] for r in members}) > 1:
            cross_class_collisions += 1
    if cross_class_collisions:
        warnings.append(
            f"{cross_class_collisions} perceptual-hash group(s) span multiple classes "
            "(kept all — possible mislabel or hash collision; review excluded/manifest if accuracy looks odd)")
    records[:] = [r for r in records if r["source_relpath"] not in drop_paths]


# ------------------------------------------------------------- split + write

def assign_splits(records: list[dict], excluded: list[dict], seed: int,
                  val_frac: float, test_frac: float,
                  max_per_class: int) -> dict[str, dict[str, int]]:
    """Deterministic per-class shuffle, optional cap, then slice val/test/train."""
    by_class: dict[str, list[dict]] = {}
    for r in records:
        by_class.setdefault(r["final_class"], []).append(r)

    counts: dict[str, dict[str, int]] = {"train": {}, "val": {}, "test": {}}
    kept: list[dict] = []
    for cls in sorted(by_class):
        items = by_class[cls]
        items.sort(key=lambda r: (r["sha256"], r["source_relpath"]))
        random.Random(f"{seed}|{cls}").shuffle(items)
        if max_per_class > 0 and len(items) > max_per_class:
            for r in items[max_per_class:]:
                excluded.append({"dataset": r["dataset"], "source_relpath": r["source_relpath"],
                                 "source_class": r["source_class"], "reason": "over_class_cap",
                                 "detail": f"max_per_class={max_per_class}"})
            items = items[:max_per_class]
        n = len(items)
        n_val = int(round(n * val_frac))
        n_test = int(round(n * test_frac))
        if val_frac > 0 and 3 <= n and n_val == 0:
            n_val = 1
        if test_frac > 0 and 5 <= n and n_test == 0:
            n_test = 1
        while n_val + n_test > max(0, n - 1):
            if n_val >= n_test and n_val > 0:
                n_val -= 1
            elif n_test > 0:
                n_test -= 1
            else:
                break
        for i, r in enumerate(items):
            r["split"] = "val" if i < n_val else ("test" if i < n_val + n_test else "train")
            kept.append(r)
        counts["train"][cls] = n - n_val - n_test
        counts["val"][cls] = n_val
        counts["test"][cls] = n_test
    records[:] = kept
    return counts


def write_outputs(out: Path, records: list[dict], excluded: list[dict],
                  config: dict, counts: dict, warnings: list[str],
                  canonical: list[str], dataset_id: str,
                  source_root: Path, mapping: dict,
                  dry_run: bool) -> None:
    if dry_run:
        print("[dry-run] no files written.")
        return
    for name in GENERATED_DIRS:
        shutil.rmtree(out / name, ignore_errors=True)
    for name in GENERATED_FILES:
        (out / name).unlink(missing_ok=True)
    for split in ("train", "val", "test"):
        for r in records:
            if r["split"] != split:
                continue
            dst = out / split / r["final_class"] / r["path"].name
            if dst.exists():  # same basename from two source folders
                dst = dst.with_name(f"{r['path'].stem}_{r['sha256'][:8]}{r['path'].suffix}")
            copy_image(r["path"], dst, strip_exif=config["strip_exif"])
            r["output_relpath"] = str(dst.relative_to(out)).replace("\\", "/")

    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        for r in sorted(records, key=lambda r: r["source_relpath"]):
            w.writerow({k: r.get(k, "") for k in MANIFEST_FIELDS})
    with open(out / "excluded_images.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=EXCLUDED_FIELDS)
        w.writeheader()
        for r in sorted(excluded, key=lambda r: r["source_relpath"]):
            w.writerow(r)

    by_reason: dict[str, int] = {}
    for r in excluded:
        by_reason[r["reason"]] = by_reason.get(r["reason"], 0) + 1
    summary = {
        "dataset": dataset_id,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_root": str(source_root),
        "output_root": str(out),
        "source": {k: mapping[k] for k in ("title", "author", "url", "license") if k in mapping},
        "config": config,
        "classes": canonical,
        "counts": counts,
        "totals": {"source_files": len(records) + len(excluded),
                   "kept": len(records), "excluded": len(excluded)},
        "excluded_by_reason": by_reason,
        "warnings": warnings,
    }
    (out / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    names_lines = [f"  {i}: {c}" for i, c in enumerate(canonical)]
    (out / "data.yaml").write_text(
        "# Generated by ml/prepare_dataset.py from ml/classes.json — do not edit.\n"
        f"path: {str(out).replace(chr(92), '/')}\n"
        "train: train\nval: val\ntest: test\n\nnames:\n" + "\n".join(names_lines) + "\n",
        encoding="utf-8")

    map_rows = "\n".join(f"| `{s}` | `{t}` |" for s, t in sorted(mapping["map"].items()))
    count_rows = "\n".join(
        f"| {c} | {counts['train'].get(c, 0)} | {counts['val'].get(c, 0)} | {counts['test'].get(c, 0)} |"
        for c in canonical)
    (out / "README.md").write_text(
        f"# LoopWise training dataset ({dataset_id})\n\n"
        "Generated by `ml/prepare_dataset.py` — do not edit by hand; re-run the script instead.\n\n"
        "## Provenance\n\n"
        f"- Source: {mapping.get('title', '?')} — {mapping.get('author', '?')}\n"
        f"- URL: {mapping.get('url', '?')}\n"
        f"- License: {mapping.get('license', '?')}\n"
        f"- Raw copy (read-only): `{source_root}`\n"
        f"- Generated (UTC): {summary['generated_at']}\n"
        f"- Command config: seed={config['seed']}, val_frac={config['val_frac']}, "
        f"test_frac={config['test_frac']}, max_per_class={config['max_per_class']}, "
        f"strip_exif={config['strip_exif']}\n\n"
        "## Source label to model class mapping\n\n"
        "| source folder | model class |\n|---|---|\n" + map_rows + "\n\n"
        "## Counts (train / val / test)\n\n"
        "| class | train | val | test |\n|---|---|---|---|\n" + count_rows + "\n\n"
        f"Kept {len(records)} of {len(records) + len(excluded)} source images "
        f"({len(excluded)} excluded; see `excluded_images.csv`).\n\n"
        "## Caveats\n\n"
        "- Broad material classes only — the model cannot identify subtypes "
        "(plastic resin, battery chemistry, glass colour).\n"
        "- Source labels are the original dataset's labels; label noise in the source "
        "propagates to this dataset.\n"
        "- Photos are re-copied without EXIF metadata when Pillow is available.\n",
        encoding="utf-8")


# ----------------------------------------------------------------------- main

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Prepare the LoopWise training dataset (stdlib only).")
    ap.add_argument("--source-root", required=True, help="Raw folder-per-class dataset root (never modified)")
    ap.add_argument("--out", required=True, help="Output dataset root (train/val/test + manifest)")
    ap.add_argument("--dataset", default="kaggle12", help="Dataset id in the mapping file (default: %(default)s)")
    ap.add_argument("--mapping", default=str(repo_root / "ml" / "source_mapping.json"),
                    help="Path to source label mapping JSON")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--test-frac", type=float, default=0.1)
    ap.add_argument("--max-per-class", type=int, default=0,
                    help="Cap images per class after dedupe (0 = no cap)")
    ap.add_argument("--keep-exif", action="store_true", help="Copy files verbatim instead of stripping EXIF")
    ap.add_argument("--no-near-dup", action="store_true",
                    help="Keep perceptual near-duplicates within a class (skip dHash dedupe)")
    ap.add_argument("--dry-run", action="store_true", help="Compute and report, write nothing")
    ap.add_argument("--force", action="store_true", help="Rebuild an existing output directory")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not (0 <= args.val_frac < 1 and 0 <= args.test_frac < 1
            and args.val_frac + args.test_frac < 1):
        print("ERROR: --val-frac/--test-frac must be in [0,1) and sum to < 1", file=sys.stderr)
        return 1
    repo_root = Path(__file__).resolve().parent.parent
    source_root = Path(args.source_root)
    if not source_root.is_absolute():
        source_root = (Path.cwd() / source_root).resolve()
    out = Path(args.out)
    if not out.is_absolute():
        out = (Path.cwd() / out).resolve()

    try:
        canonical = load_canonical(repo_root)
        mapping = load_mapping(Path(args.mapping), args.dataset)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if not source_root.is_dir():
        print(f"ERROR: source root not found: {source_root}", file=sys.stderr)
        return 2

    existing = [n for n in (*GENERATED_DIRS, *GENERATED_FILES) if (out / n).exists()]
    if existing and not args.force:
        print(f"ERROR: output {out} already contains {existing}. Re-run with --force to rebuild.",
              file=sys.stderr)
        return 2

    try:
        records, excluded, warnings = scan_source(source_root, mapping, args.dataset, canonical)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    n_source = len(records) + len(excluded)
    dedupe(records, excluded, warnings, near_dup=not args.no_near_dup)
    counts = assign_splits(records, excluded, args.seed, args.val_frac,
                           args.test_frac, args.max_per_class)

    config = {"seed": args.seed, "val_frac": args.val_frac, "test_frac": args.test_frac,
              "max_per_class": args.max_per_class, "strip_exif": not args.keep_exif,
              "near_dup": not args.no_near_dup,
              "mapping_file": str(Path(args.mapping).resolve()), "pillow_available": _HAVE_PIL}
    print(f"Source      : {source_root}")
    print(f"Output      : {out}")
    print(f"Dataset     : {args.dataset}  classes={len(canonical)}")
    print(f"Scanned     : {n_source} files | kept {len(records)} | excluded {len(excluded)}")
    for split in ("train", "val", "test"):
        detail = ", ".join(f"{c}={counts[split].get(c, 0)}" for c in canonical)
        print(f"[{split}] total={sum(counts[split].values())} | {detail}")
    by_reason: dict[str, int] = {}
    for r in excluded:
        by_reason[r["reason"]] = by_reason.get(r["reason"], 0) + 1
    if by_reason:
        print("Excluded   : " + ", ".join(f"{k}={v}" for k, v in sorted(by_reason.items())))
    for w in warnings:
        print(f"WARN: {w}")

    try:
        if not args.dry_run:
            out.mkdir(parents=True, exist_ok=True)
        write_outputs(out, records, excluded, config, counts, warnings, canonical,
                      args.dataset, source_root, mapping, args.dry_run)
    except OSError as e:
        print(f"ERROR: could not write outputs: {e}", file=sys.stderr)
        return 2
    if not args.dry_run:
        print(f"\nWrote dataset. Next: python ml/validate_dataset.py --data {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

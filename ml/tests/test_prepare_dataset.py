"""Tests for ml/prepare_dataset.py (stdlib + Pillow; run from any venv).

Run:  backend/.venv/Scripts/python -m pytest ml/tests/test_prepare_dataset.py
"""

import csv
import json
import random
import shutil
from pathlib import Path

import pytest
from PIL import Image

import prepare_dataset as pd

ML_DIR = Path(__file__).resolve().parents[1]
_CLASSES = json.loads((ML_DIR / "classes.json").read_text(encoding="utf-8"))
CANONICAL = [_CLASSES[str(i)] for i in range(len(_CLASSES))]


def make_image(path: Path, seed: int, size=(16, 16)) -> None:
    """Deterministic noise image (distinct content per seed => distinct dHash)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    im = Image.new("RGB", size)
    px = im.load()
    for y in range(size[1]):
        for x in range(size[0]):
            px[x, y] = (rng.randrange(256), rng.randrange(256), rng.randrange(256))
    im.save(path)


@pytest.fixture
def raw_source(tmp_path):
    src = tmp_path / "raw"
    for i in range(25):
        make_image(src / "plastic" / f"p{i}.jpg", seed=100 + i)
    for i in range(25):
        make_image(src / "biological" / f"b{i}.jpg", seed=200 + i)
    shutil.copyfile(src / "plastic" / "p0.jpg", src / "plastic" / "p0_copy.jpg")  # exact dup
    make_image(src / "mystery" / "m0.jpg", seed=999)   # unmapped source folder
    make_image(src / "loose.jpg", seed=888)            # file directly in source root
    return src


def run_prepare(raw, out, *extra):
    return pd.main(["--source-root", str(raw), "--out", str(out),
                    "--dataset", "kaggle12", *extra])


def test_prepare_end_to_end(raw_source, tmp_path):
    out = tmp_path / "dataset"
    assert run_prepare(raw_source, out) == 0
    summary = json.loads((out / "dataset_summary.json").read_text(encoding="utf-8"))

    assert summary["totals"]["kept"] == 50          # 25 plastic + 25 biological
    assert summary["excluded_by_reason"]["duplicate_exact"] == 1
    assert summary["excluded_by_reason"]["unmapped_source_label"] == 1
    assert summary["excluded_by_reason"]["loose_file"] == 1

    # 25 per class with val/test frac 0.1 -> round(2.5) == 2 each, 21 train
    for cls in ("plastic", "organic"):
        assert summary["counts"]["train"][cls] == 21
        assert summary["counts"]["val"][cls] == 2
        assert summary["counts"]["test"][cls] == 2
    for split in ("train", "val", "test"):
        for cls in ("plastic", "organic"):
            n_files = len(list((out / split / cls).glob("*.jpg")))
            assert n_files == summary["counts"][split][cls]

    rows = list(csv.DictReader((out / "manifest.csv").open(encoding="utf-8")))
    assert len(rows) == 50
    assert all(r["split"] in ("train", "val", "test") for r in rows)
    assert all(r["output_relpath"] for r in rows)

    yaml_text = (out / "data.yaml").read_text(encoding="utf-8")
    for i, name in enumerate(CANONICAL):
        assert f"{i}: {name}" in yaml_text

    assert (out / "README.md").is_file()
    # raw source is never modified
    assert (raw_source / "plastic" / "p0_copy.jpg").exists()
    assert (raw_source / "loose.jpg").exists()
    assert len(list((raw_source / "plastic").glob("*.jpg"))) == 26


def test_prepare_is_deterministic(raw_source, tmp_path):
    out1, out2 = tmp_path / "d1", tmp_path / "d2"
    assert run_prepare(raw_source, out1) == 0
    assert run_prepare(raw_source, out2) == 0
    assert (out1 / "manifest.csv").read_text(encoding="utf-8") == \
           (out2 / "manifest.csv").read_text(encoding="utf-8")


def test_dry_run_writes_nothing(raw_source, tmp_path):
    out = tmp_path / "dry"
    assert run_prepare(raw_source, out, "--dry-run") == 0
    assert not out.exists()


def test_existing_output_requires_force(raw_source, tmp_path):
    out = tmp_path / "ds"
    assert run_prepare(raw_source, out) == 0
    assert run_prepare(raw_source, out) == 2          # refuses to clobber
    assert run_prepare(raw_source, out, "--force") == 0


def test_max_per_class_caps_and_excludes(raw_source, tmp_path):
    out = tmp_path / "cap"
    assert run_prepare(raw_source, out, "--max-per-class", "10") == 0
    summary = json.loads((out / "dataset_summary.json").read_text(encoding="utf-8"))
    assert summary["totals"]["kept"] == 20
    assert summary["excluded_by_reason"]["over_class_cap"] == 30
    assert summary["counts"]["train"]["plastic"] == 8
    assert summary["counts"]["val"]["plastic"] == 1
    assert summary["counts"]["test"]["plastic"] == 1


def test_unknown_dataset_id_errors(raw_source, tmp_path):
    assert pd.main(["--source-root", str(raw_source), "--out", str(tmp_path / "x"),
                    "--dataset", "does-not-exist"]) == 2

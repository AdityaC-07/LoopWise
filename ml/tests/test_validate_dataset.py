"""Tests for ml/validate_dataset.py (stdlib; run from any venv).

Run:  backend/.venv/Scripts/python -m pytest ml/tests/test_validate_dataset.py
"""

import json
import random
import shutil
from pathlib import Path

from PIL import Image

import validate_dataset as vd

ML_DIR = Path(__file__).resolve().parents[1]
_CLASSES = json.loads((ML_DIR / "classes.json").read_text(encoding="utf-8"))
CANONICAL = [_CLASSES[str(i)] for i in range(len(_CLASSES))]


def make_image(path: Path, seed: int, size=(16, 16)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    im = Image.new("RGB", size)
    px = im.load()
    for y in range(size[1]):
        for x in range(size[0]):
            px[x, y] = (rng.randrange(256), rng.randrange(256), rng.randrange(256))
    im.save(path)


def build_dataset(root: Path, n: int = 20, classes=None) -> Path:
    classes = list(classes or CANONICAL)
    for si, split in enumerate(("train", "val", "test")):
        for ci, cls in enumerate(classes):
            for i in range(n):
                make_image(root / split / cls / f"{split}_{cls}_{i}.jpg",
                           seed=si * 100000 + ci * 1000 + i)
    return root


def test_validate_passes(tmp_path, capsys):
    root = build_dataset(tmp_path / "ds")
    assert vd.main(["--data", str(root)]) == 0
    assert "VALIDATION PASSED" in capsys.readouterr().out


def test_validate_writes_json(tmp_path):
    root = build_dataset(tmp_path / "ds")
    report = tmp_path / "report.json"
    assert vd.main(["--data", str(root), "--json", str(report)]) == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["passed"] is True
    assert data["counts"]["train"]["plastic"] == 20
    assert data["hash_check"] is True


def test_missing_class_fails(tmp_path, capsys):
    root = build_dataset(tmp_path / "ds", classes=CANONICAL[:-1])  # no textile
    assert vd.main(["--data", str(root)]) == 2
    assert "missing class directory" in capsys.readouterr().out


def test_hash_leakage_detected(tmp_path, capsys):
    root = build_dataset(tmp_path / "ds")
    src = root / "train" / "plastic" / "train_plastic_0.jpg"
    shutil.copyfile(src, root / "val" / "plastic" / "renamed_leak.jpg")
    assert vd.main(["--data", str(root)]) == 2
    assert "identical image bytes" in capsys.readouterr().out


def test_bad_signature_detected(tmp_path, capsys):
    root = build_dataset(tmp_path / "ds")
    (root / "train" / "plastic" / "train_plastic_0.jpg").write_bytes(b"this is not an image")
    assert vd.main(["--data", str(root)]) == 2
    assert "bad signature" in capsys.readouterr().out


def test_missing_root_fails(tmp_path, capsys):
    assert vd.main(["--data", str(tmp_path / "nope")]) == 2
    assert "Dataset root not found" in capsys.readouterr().out


def test_consistency_helper():
    assert vd.check_consistency(["a", "b"], ["a", "b"]) == []
    assert vd.check_consistency(["a", "b"], ["b", "a"])
    assert vd.check_consistency(["a"], None)
    assert vd.load_data_yaml_names(ML_DIR.parent) is not None


def test_auto_split_creates_val(tmp_path):
    root = tmp_path / "ds"
    for ci, cls in enumerate(CANONICAL):
        for i in range(110):
            make_image(root / "train" / cls / f"{cls}_{i}.jpg", seed=ci * 1000 + i)
    rc = vd.main(["--data", str(root), "--auto-split", "0.2"])
    assert (root / "val" / "plastic").is_dir()
    assert rc == 0  # test/ absent is a warning, not an error

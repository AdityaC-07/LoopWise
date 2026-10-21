"""ONNX inference contract: output semantics, preprocessing parity, safety.

These tests exist because a production-blocking bug shipped: the backend
softmaxed an ONNX output that was ALREADY a valid probability distribution.
For 8 classes that caps every confidence at e/(e+7) ~= 0.2797, below
LOW_CONFIDENCE_THRESHOLD=0.35, so every image resolved to "unknown".

The tests lock down the corrected contract:
  * a probability distribution is validated and used directly (never re-softmaxed)
  * raw logits are softmaxed ONLY when the model is explicitly configured as
    a logits model
  * malformed outputs (bad shape, NaN/inf, negatives, bad sums) are rejected
  * class ordering follows the class-index map
  * the shipped preprocessing matches the reference Ultralytics transform
  * the real ONNX artefact is exercised end-to-end when available (else skipped)
"""

import json
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.services.inference.onnx_classifier import (
    ONNXClassifier,
    ModelOutputError,
    DEFAULT_OUTPUT_SEMANTICS,
    LOW_CONFIDENCE_THRESHOLD,
)
from app.services.inference.preprocess import preprocess_image

REPO_ROOT = Path(__file__).resolve().parents[2]
ONNX_PATH = REPO_ROOT / "ml" / "models" / "loopwise-yolo26n-cls.onnx"
CLASS_MAP_PATH = REPO_ROOT / "ml" / "models" / "loopwise-yolo26n-cls.class-index-map.json"
TEST_DATA_DIR = REPO_ROOT / "ml" / "data" / "waste-classify" / "test"

CLASSES = {
    0: "battery_hazardous", 1: "glass", 2: "metal", 3: "organic",
    4: "other_residue", 5: "paper_cardboard", 6: "plastic", 7: "textile",
}


def _bare_classifier(semantics: str = "probabilities", mapping=None) -> ONNXClassifier:
    """Build an ONNXClassifier without loading the model (unit-test helper)."""
    clf = object.__new__(ONNXClassifier)
    clf._index_to_class = dict(mapping if mapping is not None else CLASSES)
    clf._output_semantics = semantics
    clf._input_shape = [1, 3, 224, 224]
    clf._input_name = "images"
    clf._model_path = "test"
    clf._model_version = "test-v1"
    return clf


# --- 1 & 2: probabilities must not be softmaxed again --------------------

def test_probability_output_is_not_softmaxed_again():
    clf = _bare_classifier()
    vec = [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.86]  # sums to 1.0
    probs = clf._interpret_output([vec])
    # unchanged (a second softmax would compress the max to ~0.28)
    assert probs == pytest.approx(vec, abs=1e-9)
    assert max(probs) == pytest.approx(0.86, abs=1e-9)


def test_eight_class_vector_retains_original_max_confidence():
    clf = _bare_classifier()
    vec = [0.93] + [0.01] * 7  # 0.93 + 0.07 = 1.00
    probs = clf._interpret_output([vec])
    ids, confs = clf._rank(probs)
    assert confs[0] == pytest.approx(0.93, abs=1e-9)
    assert ids[0] == 0


# --- 3: logits only when explicitly configured ---------------------------

def test_logits_only_handled_when_configured_as_logits():
    logits = [[2.0, 1.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]]

    # Default (probabilities): a raw-logits vector is NOT a distribution -> reject.
    clf_probs = _bare_classifier("probabilities")
    with pytest.raises(ModelOutputError):
        clf_probs._interpret_output(logits)

    # Explicit logits: stable softmax applied.
    clf_logits = _bare_classifier("logits")
    probs = clf_logits._interpret_output(logits)
    assert sum(probs) == pytest.approx(1.0, abs=1e-9)
    assert probs[0] == max(probs)


# --- 4: malformed / inconsistent outputs are rejected safely -------------

def test_wrong_class_count_rejected():
    clf = _bare_classifier()
    with pytest.raises(ModelOutputError):
        clf._interpret_output([[0.5, 0.5]])


def test_nan_rejected():
    clf = _bare_classifier()
    vec = [0.125] * 8
    vec[0] = float("nan")
    with pytest.raises(ModelOutputError):
        clf._interpret_output([vec])


def test_infinity_rejected():
    clf = _bare_classifier()
    vec = [0.125] * 8
    vec[3] = float("inf")
    with pytest.raises(ModelOutputError):
        clf._interpret_output([vec])


def test_negative_probability_rejected():
    clf = _bare_classifier()
    vec = [1.0, -1e-3] + [0.0] * 6  # sums ~0.999 but contains a negative
    with pytest.raises(ModelOutputError):
        clf._interpret_output([vec])


def test_invalid_probability_sum_rejected():
    clf = _bare_classifier()
    with pytest.raises(ModelOutputError):
        clf._interpret_output([[0.5] * 8])  # sums to 4.0


def test_rank3_output_rejected():
    clf = _bare_classifier()
    with pytest.raises(ModelOutputError):
        clf._interpret_output([[[0.125] * 8]])


def test_non_list_output_rejected():
    clf = _bare_classifier()
    with pytest.raises(ModelOutputError):
        clf._interpret_output(0.5)


# --- 5: class ordering matches the class-index map -----------------------

def test_class_ordering_matches_map():
    clf = _bare_classifier()
    vec = [0.01] * 8
    vec[6] = 0.93  # index 6 == plastic
    ids, confs = clf._rank(clf._interpret_output([vec]))
    assert ids[0] == 6
    assert clf._index_to_class[ids[0]] == "plastic"


def test_shipped_class_map_matches_taxonomy():
    if not CLASS_MAP_PATH.is_file():
        pytest.skip(f"class map not available: {CLASS_MAP_PATH}")
    raw = json.loads(CLASS_MAP_PATH.read_text(encoding="utf-8"))
    mapping = {int(k): str(v) for k, v in raw.items()}
    assert mapping == CLASSES


# --- 6: top-three predictions and confidences ----------------------------

def test_top3_matches_reference_ranking():
    clf = _bare_classifier()
    vec = [0.70, 0.10, 0.08, 0.05, 0.03, 0.02, 0.01, 0.01]  # sums to 1.00
    ids, confs = clf._rank(clf._interpret_output([vec]))
    assert ids[:3] == [0, 1, 2]
    assert confs[:3] == pytest.approx([0.70, 0.10, 0.08], abs=1e-9)
    assert confs[:3] == sorted(confs[:3], reverse=True)


# --- 7: low-confidence still uses the safe unknown behaviour -------------

def test_low_confidence_uses_safe_unknown():
    clf = _bare_classifier()
    res = clf._unknown_result(0.20, [0, 1, 2], [0.20, 0.18, 0.16])
    assert res.predicted_class == "unknown"
    assert res.confidence_label == "low"
    assert not hasattr(res, "is_demo")
    assert len(res.top3) == 3
    assert res.top3[0]["class"] == "unknown"


def test_low_confidence_threshold_unchanged():
    # Task constraint: do not change the threshold as part of this fix.
    assert LOW_CONFIDENCE_THRESHOLD == 0.35


# --- 8: missing model / class map fails safe -----------------------------

def test_missing_model_file_raises():
    with pytest.raises(FileNotFoundError):
        ONNXClassifier(model_path=str(REPO_ROOT / "ml" / "models" / "does-not-exist.onnx"))


def test_missing_class_map_is_empty_and_fails_safe():
    clf = object.__new__(ONNXClassifier)
    assert clf._load_class_map(None) == {}
    assert clf._load_class_map(str(REPO_ROOT / "no-such-map.json")) == {}


def test_factory_rejects_missing_model_without_mock_fallback(monkeypatch):
    from app.services.inference import factory
    from app.core.errors import InferenceConfigurationError

    monkeypatch.setattr(factory.settings, "MODEL_PATH", None, raising=False)
    factory.reset_classifier_cache()
    try:
        with pytest.raises(InferenceConfigurationError):
            factory.get_classifier()
    finally:
        factory.reset_classifier_cache()


def test_unknown_semantics_falls_back_to_default():
    clf = object.__new__(ONNXClassifier)
    assert clf._resolve_output_semantics("nonsense") == DEFAULT_OUTPUT_SEMANTICS
    assert clf._resolve_output_semantics("LOGITS") == "logits"
    assert clf._resolve_output_semantics("probabilities") == "probabilities"


# --- preprocessing parity (deterministic geometry) -----------------------

def test_preprocess_output_shape_dtype_and_range():
    img = Image.new("RGB", (500, 300), (10, 20, 30))
    out = preprocess_image(img, 224)
    assert out.shape == (1, 3, 224, 224)
    assert out.dtype == np.float32
    assert out.min() >= 0.0 and out.max() <= 1.0


def test_preprocess_landscape_matches_center_crop():
    arr = np.zeros((224, 448, 3), np.uint8)
    for x in range(448):
        arr[:, x, :] = x % 256
    img = Image.fromarray(arr, "RGB")
    out = preprocess_image(img, 224)  # no resize needed, centre crop only
    exp = np.asarray(img.crop((112, 0, 336, 224)), np.float32) / 255.0
    exp = np.transpose(exp, (2, 0, 1))[None]
    assert np.allclose(out, exp, atol=1e-6)


def test_preprocess_portrait_matches_center_crop():
    arr = np.zeros((448, 224, 3), np.uint8)
    for y in range(448):
        arr[y, :, :] = y % 256
    img = Image.fromarray(arr, "RGB")
    out = preprocess_image(img, 224)  # no resize needed, centre crop only
    exp = np.asarray(img.crop((0, 112, 224, 336)), np.float32) / 255.0
    exp = np.transpose(exp, (2, 0, 1))[None]
    assert np.allclose(out, exp, atol=1e-6)


def test_preprocess_resizes_shortest_edge():
    # 100x50 -> shortest edge 100 -> 224 => (224, 448), then centre crop 224.
    img = Image.new("RGB", (100, 50), (0, 0, 0))
    out = preprocess_image(img, 224)
    assert out.shape == (1, 3, 224, 224)


# --- 9: real ONNX artifact integration -----------------------------------

def _collect_test_images(limit: int = 15):
    if not TEST_DATA_DIR.is_dir():
        return []
    images = []
    for cls_dir in sorted(TEST_DATA_DIR.iterdir()):
        if not cls_dir.is_dir():
            continue
        for p in sorted(cls_dir.iterdir()):
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                images.append(p)
                if len(images) >= limit:
                    return images
    return images


@pytest.mark.asyncio
async def test_real_onnx_artifact_integration():
    """End-to-end on the REAL artifact. Skips (explicitly) if unavailable.

    Never substitutes synthetic logits: the assertion that at least one real
    image exceeds LOW_CONFIDENCE_THRESHOLD is exactly what the double-softmax
    bug violated (its ceiling is e/(e+7) ~= 0.2797 < 0.35).
    """
    if not ONNX_PATH.is_file():
        pytest.skip(f"ONNX artifact not available: {ONNX_PATH}")
    if not CLASS_MAP_PATH.is_file():
        pytest.skip(f"class map not available: {CLASS_MAP_PATH}")
    images = _collect_test_images()
    if not images:
        pytest.skip(f"test dataset not available: {TEST_DATA_DIR}")

    clf = ONNXClassifier(model_path=str(ONNX_PATH), class_index_map=str(CLASS_MAP_PATH))

    results = []
    for p in images:
        results.append(await clf.classify(image_bytes=p.read_bytes()))

    # Every result is genuine and numerically sane.
    for res in results:
        assert not hasattr(res, "is_demo")
        assert math.isfinite(res.confidence)
        assert 0.0 <= res.confidence <= 1.0
        assert len(res.top3) == 3
        assert res.top3[0]["class"] == res.predicted_class
        assert [t["confidence"] for t in res.top3] == sorted(
            [t["confidence"] for t in res.top3], reverse=True
        )

    # The bug would make EVERY prediction unknown; after the fix real inputs
    # must produce confident, non-unknown predictions.
    confident = [r for r in results if r.confidence > LOW_CONFIDENCE_THRESHOLD]
    assert confident, "all predictions were rejected as unknown (double-softmax regression)"
    assert max(r.confidence for r in results) > LOW_CONFIDENCE_THRESHOLD

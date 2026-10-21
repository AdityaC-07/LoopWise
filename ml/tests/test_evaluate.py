"""Multi-resolution support: 224 (V1) and 384 (V2) models in one evaluator.

The offline evaluator used to hardcode a 224 input. The V2 artefact is
384x384, so evaluating it would either crash on a shape mismatch or — far
worse — silently resample to 224 and measure a pipeline nobody deploys.

These tests lock down:
  * input size is DERIVED from the ONNX metadata (224 for V1, 384 for V2)
  * an explicit --imgsz override wins
  * the shipped backend transform is bit-exact against the reference at BOTH
    resolutions, so switching model version cannot silently change geometry
  * the V1 (224) numbers and behaviour are unchanged by the refactor
"""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import evaluate as ev

REPO_ROOT = Path(__file__).resolve().parents[2]
V1_ONNX = REPO_ROOT / "ml" / "models" / "loopwise-yolo26n-cls.onnx"
V2_ONNX = REPO_ROOT / "ml" / "models" / "loopwise-yolo26s-cls-v2.onnx"


class _FakeInput:
    def __init__(self, shape):
        self.shape = shape


# --- input size derivation -------------------------------------------------

def test_derives_224_for_v1_shape():
    assert ev.derive_input_size(_FakeInput([1, 3, 224, 224]))[0] == 224


def test_derives_384_for_v2_shape():
    size, note = ev.derive_input_size(_FakeInput([1, 3, 384, 384]))
    assert size == 384
    assert "derived from ONNX input shape" in note


def test_derives_384_from_dynamic_batch_dimension():
    # Ultralytics exports often leave the batch dim as a symbolic string.
    assert ev.derive_input_size(_FakeInput(["batch", 3, 384, 384]))[0] == 384


def test_non_square_input_uses_shorter_edge():
    size, note = ev.derive_input_size(_FakeInput([1, 3, 384, 640]))
    assert size == 384
    assert "non-square" in note


def test_unusable_metadata_falls_back_to_224():
    size, note = ev.derive_input_size(_FakeInput([1, 3, "h", "w"]))
    assert size == 224
    assert "WARN" in note


def test_imgsz_override_wins_over_metadata():
    args = ev.parse_args([
        "--onnx", "x.onnx", "--class-map", "m.json", "--data", "d",
        "--splits", "test", "--out", "o", "--imgsz", "256",
    ])
    assert args.imgsz == 256


def test_imgsz_defaults_to_zero_mean_auto():
    args = ev.parse_args([
        "--onnx", "x.onnx", "--class-map", "m.json", "--data", "d",
        "--splits", "test", "--out", "o",
    ])
    assert args.imgsz == 0


# --- the real artefacts report their true resolution ------------------------

def test_v1_artefact_reports_224():
    if not V1_ONNX.is_file():
        pytest.skip(f"V1 artefact not present: {V1_ONNX}")
    import onnxruntime as ort
    assert ev.derive_input_size(ort.InferenceSession(str(V1_ONNX)).get_inputs()[0])[0] == 224


def test_v2_artefact_reports_384():
    if not V2_ONNX.is_file():
        pytest.skip(f"V2 artefact not present: {V2_ONNX}")
    import onnxruntime as ort
    size, _ = ev.derive_input_size(ort.InferenceSession(str(V2_ONNX)).get_inputs()[0])
    assert size == 384


# --- preprocessing parity at both resolutions -------------------------------

def _sample_image(w: int = 500, h: int = 300) -> Image.Image:
    """Deterministic, non-square image that exercises resize + centre crop."""
    rng = np.random.default_rng(0)
    return Image.fromarray(rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8))


@pytest.mark.parametrize("size", [224, 384])
def test_backend_preprocess_matches_reference_at_both_resolutions(size):
    tv = pytest.importorskip("torchvision")
    from torchvision import transforms as T

    img = _sample_image()
    ref = T.Compose([
        T.Resize(size, interpolation=T.InterpolationMode.BILINEAR),
        T.CenterCrop(size),
        T.ToTensor(),
    ])(img.convert("RGB")).numpy()[np.newaxis, ...]

    # The backend transform is loaded exactly as the evaluator loads it, so
    # this test fails if either side drifts.
    backend = ev.build_transform("backend", size)
    got = backend(img, size)

    assert got.shape == (1, 3, size, size)
    assert got.dtype == np.float32
    # Bit-exact: same geometry, same BILINEAR resampler, same /255, no mean/std.
    np.testing.assert_array_equal(got, ref)


def test_v1_224_shape_and_range_unchanged():
    # Regression lock: the refactor must not alter V1's established contract.
    out = ev.build_transform("backend", 224)(_sample_image(), 224)
    assert out.shape == (1, 3, 224, 224)
    assert out.dtype == np.float32
    assert out.min() >= 0.0 and out.max() <= 1.0


def test_v2_384_shape_and_range():
    out = ev.build_transform("backend", 384)(_sample_image(), 384)
    assert out.shape == (1, 3, 384, 384)
    assert out.dtype == np.float32
    assert out.min() >= 0.0 and out.max() <= 1.0


def test_preprocess_dispatch_passes_size_through(tmp_path):
    # --preprocess backend must forward the DERIVED size, not a hidden default.
    p = tmp_path / "img.png"
    _sample_image().save(p)
    fn = ev.build_transform("backend", 384)
    assert ev.preprocess(p, "backend", 384, fn).shape == (1, 3, 384, 384)

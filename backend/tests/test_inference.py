"""Inference service behaviour now that ONNX is the only classification path.

These tests exist because the application used to run a keyword simulator when
DEMO_MODE was on, and fell back to that simulator for text-only requests even
when a real model was loaded. That fallback is gone, so these tests lock down:

  * a real uploaded image reaches the ONNX session and the answer derives
    from the model output (never from a simulator)
  * an image alone is enough — the description is optional
  * a text-only request is rejected instead of being answered by a guess
  * a missing/broken model raises an explicit service error and NEVER returns
    a fabricated classification
  * a genuine low-confidence "unknown" is distinct from a backend failure
  * malformed / unsupported / unreadable uploads are user-facing input errors,
    not service errors, and never become "unknown item" predictions
"""

import base64
import io
import uuid

import numpy as np
import pytest
from PIL import Image

from app.core.errors import (
    InferenceConfigurationError,
    InferenceFailedError,
    InvalidInputError,
    UnsupportedFormatError,
)
from app.services.inference import factory
from app.services.inference.onnx_classifier import LOW_CONFIDENCE_THRESHOLD
from app.services.inference.result import ClassificationResult

BROAD_CLASSES = {
    0: "battery_hazardous", 1: "glass", 2: "metal", 3: "organic",
    4: "other_residue", 5: "paper_cardboard", 6: "plastic", 7: "textile",
}


def _jpeg_bytes(size=(320, 240), color=(200, 40, 40)) -> bytes:
    """A real, decodable JPEG — not a magic-byte stub."""
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _classify_payload(image_bytes=None, description=None, **extra):
    payload = {
        "session_id": str(uuid.uuid4()),
        "input_type": "image" if image_bytes is not None else "text",
        "consent": {"image_upload": False, "analytics": True, "location": False},
    }
    if image_bytes is not None:
        payload["image_b64"] = _b64(image_bytes)
    if description is not None:
        payload["description"] = description
    payload.update(extra)
    return payload


def _vector(top_index: int, top_value: float = 0.9) -> np.ndarray:
    """A valid probability vector (sums to 1) peaking at top_index."""
    rest = (1.0 - top_value) / 7.0
    vec = np.full(8, rest, dtype=np.float32)
    vec[top_index] = top_value
    return vec


@pytest.fixture()
def live_classifier(monkeypatch):
    """The real ONNX classifier the factory hands out, with a fake session.

    ``fake_output`` is set per-test; ``fake_run`` records the tensors the
    session received so tests can prove the uploaded image reached inference.
    """
    factory.reset_classifier_cache()
    clf = factory.get_classifier()
    calls = {}

    def _install(output):
        calls["output"] = output

        def fake_run(output_ids, feed):
            calls["feeds"] = feed
            calls["input_name"] = list(feed.keys())[0]
            arr = next(iter(feed.values()))
            calls["tensor_shape"] = tuple(arr.shape)
            calls["tensor_dtype"] = arr.dtype
            return [output]

        monkeypatch.setattr(clf._session, "run", fake_run)

    calls["install"] = _install
    calls["classifier"] = clf
    yield calls
    factory.reset_classifier_cache()


# --- 1: a real upload reaches the ONNX session -----------------------------

@pytest.mark.asyncio
async def test_uploaded_image_reaches_onnx_session(live_classifier):
    """The uploaded bytes are preprocessed into a real tensor and fed to ONNX."""
    live_classifier["install"](_vector(6, 0.97))  # index 6 == plastic
    clf = live_classifier["classifier"]

    res = await clf.classify(image_bytes=_jpeg_bytes())

    assert live_classifier["input_name"] in ("images", "input")
    assert live_classifier["tensor_shape"] == (1, 3, 224, 224)
    assert live_classifier["tensor_dtype"] == np.float32
    assert res.predicted_class == "plastic"
    assert res.confidence == pytest.approx(0.97, abs=0.01)


@pytest.mark.asyncio
async def test_classification_result_derives_from_model_output(live_classifier):
    """Changing the model output changes the answer — no canned result exists."""
    clf = live_classifier["classifier"]

    live_classifier["install"](_vector(2, 0.9))  # metal
    metal = await clf.classify(image_bytes=_jpeg_bytes())

    live_classifier["install"](_vector(0, 0.9))  # battery_hazardous
    battery = await clf.classify(image_bytes=_jpeg_bytes())

    assert metal.predicted_class == "metal"
    assert battery.predicted_class == "battery_hazardous"
    assert metal.event_id != battery.event_id


@pytest.mark.asyncio
async def test_result_carries_no_demo_flag_and_a_real_model_version(live_classifier):
    live_classifier["install"](_vector(1, 0.88))
    res = await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes())
    assert not hasattr(res, "is_demo")
    assert res.model_version == "yolo26n-cls-v1"


@pytest.mark.asyncio
async def test_top3_is_ranked_and_explains_real_materials(live_classifier):
    live_classifier["install"](_vector(5, 0.8))
    res = await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes())
    assert len(res.top3) == 3
    assert res.top3[0]["class"] == res.predicted_class
    confs = [t["confidence"] for t in res.top3]
    assert confs == sorted(confs, reverse=True)
    assert res.material.disposal_bin in ("wet", "dry", "hazardous", "e_waste", "rejected")


# --- 2: image alone is enough; description is optional ---------------------

@pytest.mark.asyncio
async def test_image_only_with_empty_description_classifies(live_classifier):
    live_classifier["install"](_vector(3, 0.92))  # organic
    res = await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes(), description="")
    assert res.predicted_class == "organic"
    assert res.confidence > LOW_CONFIDENCE_THRESHOLD


@pytest.mark.asyncio
async def test_image_only_with_no_description_at_all(live_classifier):
    live_classifier["install"](_vector(7, 0.95))  # textile
    res = await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes())
    assert res.predicted_class == "textile"


# --- 3: text-only is rejected, never guessed -------------------------------

@pytest.mark.asyncio
async def test_text_only_request_is_rejected():
    clf = factory.get_classifier()
    with pytest.raises(InvalidInputError) as exc:
        await clf.classify(image_bytes=None, description="plastic water bottle")
    assert exc.value.status_code == 422
    assert "photo" in exc.value.message.lower()


@pytest.mark.asyncio
async def test_empty_request_is_rejected():
    with pytest.raises(InvalidInputError):
        await factory.get_classifier().classify(image_bytes=None, description=None)


# --- 4: unavailable model is an explicit error, never a mock result --------

def test_factory_never_returns_a_mock():
    factory.reset_classifier_cache()
    try:
        clf = factory.get_classifier()
        assert type(clf).__name__ == "ONNXClassifier"
        assert not hasattr(clf, "is_demo")
        assert not hasattr(clf, "keyword")  # no keyword simulator
    finally:
        factory.reset_classifier_cache()


def test_missing_model_path_is_an_explicit_configuration_error(monkeypatch):
    monkeypatch.setattr(factory.settings, "MODEL_PATH", None)
    factory.reset_classifier_cache()
    try:
        with pytest.raises(InferenceConfigurationError) as exc:
            factory.get_classifier()
        assert exc.value.status_code == 503
        assert "MODEL_PATH" in exc.value.message
    finally:
        factory.reset_classifier_cache()


def test_missing_class_map_is_an_explicit_configuration_error(monkeypatch):
    monkeypatch.setattr(factory.settings, "CLASS_INDEX_MAP", None)
    factory.reset_classifier_cache()
    try:
        with pytest.raises(InferenceConfigurationError):
            factory.get_classifier()
    finally:
        factory.reset_classifier_cache()


def test_model_file_that_cannot_be_loaded_is_an_explicit_error(monkeypatch, tmp_path):
    bogus = tmp_path / "not-a-model.onnx"
    bogus.write_bytes(b"this is definitely not an onnx graph")
    monkeypatch.setattr(factory.settings, "MODEL_PATH", str(bogus))
    factory.reset_classifier_cache()
    try:
        with pytest.raises(InferenceConfigurationError):
            factory.get_classifier()
    finally:
        factory.reset_classifier_cache()


@pytest.mark.asyncio
async def test_inference_failure_raises_and_fabricates_nothing(live_classifier):
    """A broken runtime surfaces as a service error — not an 'unknown item'."""
    def exploding_run(output_ids, feed):
        raise RuntimeError("onnxruntime blew up")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(live_classifier["classifier"]._session, "run", exploding_run)
    try:
        with pytest.raises(InferenceFailedError) as exc:
            await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes())
    finally:
        monkeypatch.undo()

    assert exc.value.status_code == 500
    assert "temporarily unavailable" in exc.value.message.lower()


@pytest.mark.asyncio
async def test_malformed_model_output_is_a_service_error(live_classifier):
    """NaN output must not become a confident prediction."""
    bad = np.full(8, np.nan, dtype=np.float32)
    live_classifier["install"](bad)
    with pytest.raises(InferenceFailedError):
        await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes())


# --- 5: unknown prediction is a real answer, distinct from an error --------

@pytest.mark.asyncio
async def test_low_confidence_returns_unknown_result_not_an_error(live_classifier):
    live_classifier["install"](_vector(4, 0.20))  # below the 0.35 threshold
    res = await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes())
    assert isinstance(res, ClassificationResult)
    assert res.predicted_class == "unknown"
    assert res.confidence_label == "low"
    assert res.confidence < LOW_CONFIDENCE_THRESHOLD
    assert res.material.disposal_bin == "rejected"
    assert "manual" in res.guidance.bin_label.lower() or "check" in res.guidance.bin_label.lower()


@pytest.mark.asyncio
async def test_unknown_result_and_service_error_are_different_outcomes(live_classifier):
    """Low confidence -> an answer to verify. Broken runtime -> an exception."""
    live_classifier["install"](_vector(4, 0.18))
    unknown = await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes())
    assert unknown.predicted_class == "unknown"          # an answer

    def exploding_run(output_ids, feed):
        raise RuntimeError("boom")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(live_classifier["classifier"]._session, "run", exploding_run)
    try:
        with pytest.raises(InferenceFailedError):
            await live_classifier["classifier"].classify(image_bytes=_jpeg_bytes())
    finally:
        monkeypatch.undo()


@pytest.mark.asyncio
async def test_unmapped_class_index_is_unknown_not_a_guess(live_classifier):
    """A class index with no guidance entry must not resolve to a wrong bin."""
    live_classifier["install"](_vector(3, 0.99))
    clf = live_classifier["classifier"]
    original = dict(clf._index_to_class)
    try:
        clf._index_to_class = {}
        res = await clf.classify(image_bytes=_jpeg_bytes())
        assert res.predicted_class == "unknown"
        assert res.material.disposal_bin == "rejected"
    finally:
        clf._index_to_class = original


# --- 6: malformed / unsupported / unreadable uploads -----------------------

@pytest.mark.asyncio
async def test_unsupported_file_format_is_a_user_error():
    """GIF bytes are rejected as unsupported input, not as a service failure."""
    gif = b"GIF89a" + b"\x00" * 32
    with pytest.raises(UnsupportedFormatError) as exc:
        await factory.get_classifier().classify(image_bytes=gif)
    assert exc.value.status_code == 415


@pytest.mark.asyncio
async def test_unreadable_but_magic_valid_image_is_a_user_error():
    """Valid JPEG magic bytes but undecodable body -> user-facing 415, not 500."""
    broken = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 128
    with pytest.raises(UnsupportedFormatError):
        await factory.get_classifier().classify(image_bytes=broken)


@pytest.mark.asyncio
async def test_truncated_image_is_a_user_error():
    truncated = _jpeg_bytes()[:40]
    with pytest.raises(UnsupportedFormatError):
        await factory.get_classifier().classify(image_bytes=truncated)


@pytest.mark.asyncio
async def test_empty_image_bytes_are_rejected_as_input():
    with pytest.raises(InvalidInputError):
        await factory.get_classifier().classify(image_bytes=b"")


# --- 7: API-level checks ---------------------------------------------------

@pytest.mark.asyncio
async def test_api_classify_image_only_with_empty_description(live_classifier):
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    live_classifier["install"](_vector(6, 0.94))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=_classify_payload(_jpeg_bytes(), description=""))
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["predicted_class"] == "plastic"
        assert body["meta"]["model_version"] == "yolo26n-cls-v1"
        assert "demo_mode" not in body["meta"]


@pytest.mark.asyncio
async def test_api_rejects_text_only(live_classifier):
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/classify",
            json=_classify_payload(None, description="plastic water bottle"),
        )
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_api_reports_service_error_not_unknown_prediction(live_classifier):
    """A backend failure must surface as INFERENCE_FAILED, never as a result."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    def exploding_run(output_ids, feed):
        raise RuntimeError("onnxruntime blew up")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(live_classifier["classifier"]._session, "run", exploding_run)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/api/v1/classify", json=_classify_payload(_jpeg_bytes()))
    finally:
        monkeypatch.undo()

    assert res.status_code == 500
    body = res.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INFERENCE_FAILED"
    assert "temporarily unavailable" in body["error"]["message"].lower()
    assert body["data"] is None  # never a fabricated classification


@pytest.mark.asyncio
async def test_api_rejects_unsupported_upload_as_input_error():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=_classify_payload(b"GIF89a" + b"\x00" * 32))
        assert res.status_code == 415
        assert res.json()["error"]["code"] == "UNSUPPORTED_FORMAT"


@pytest.mark.asyncio
async def test_api_health_reports_real_classifier_readiness(live_classifier):
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        body = res.json()
        assert body["data"]["components"]["inference_engine"] == "ok"
        assert body["data"]["model_version"] == "yolo26n-cls-v1"
        assert "demo_mode" not in body["data"]
        assert "demo_mode" not in body["meta"]


def test_factory_caches_one_classifier_across_calls():
    factory.reset_classifier_cache()
    try:
        first = factory.get_classifier()
        second = factory.get_classifier()
        assert first is second
    finally:
        factory.reset_classifier_cache()

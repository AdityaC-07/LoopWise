import base64
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


BROAD_CLASSES = {
    "battery_hazardous", "glass", "metal", "organic",
    "other_residue", "paper_cardboard", "plastic", "textile",
}


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "ok"
        assert json_data["data"]["components"]["inference_engine"] == "ok"
        assert json_data["data"]["model_version"] == "yolo26n-cls-v1"
        assert "demo_mode" not in json_data["data"]
        assert "demo_mode" not in json_data["meta"]


@pytest.mark.asyncio
async def test_classify_text_description_is_rejected():
    """Text alone cannot be classified any more — the model needs a photo."""
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "input_type": "text",
        "description": "cardboard pizza packaging box",
        "consent": {"image_upload": False, "analytics": True, "location": False}
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=payload)
        assert res.status_code == 422
        json_data = res.json()
        assert json_data["status"] == "error"
        assert json_data["error"]["code"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_classify_invalid_empty_input():
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "input_type": "text",
        "consent": {"image_upload": False, "analytics": True, "location": False}
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=payload)
        assert res.status_code == 422
        json_data = res.json()
        assert json_data["status"] == "error"
        assert json_data["error"]["code"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_classify_unknown_ward_id():
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "description": "plastic water bottle",
        "ward_id": "WD-999-INVALID",
        "consent": {"image_upload": False, "analytics": True, "location": False}
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=payload)
        assert res.status_code == 422
        json_data = res.json()
        assert json_data["error"]["code"] == "WARD_UNKNOWN"


@pytest.mark.asyncio
async def test_feedback_submission():
    session_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    payload = {
        "event_id": event_id,
        "session_id": session_id,
        "feedback_type": "correction",
        "corrected_class": "plastic_pet_bottle",
        "note": "It is actually a pet bottle"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/feedback", json=payload)
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "ok"
        assert json_data["data"]["acknowledged"] is True
        assert json_data["data"]["correction_id"] is not None


@pytest.mark.asyncio
async def test_feedback_missing_corrected_class():
    session_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    payload = {
        "event_id": event_id,
        "session_id": session_id,
        "feedback_type": "correction"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/feedback", json=payload)
        assert res.status_code == 422
        json_data = res.json()
        assert json_data["error"]["code"] in ["INVALID_CORRECTION", "INVALID_INPUT"]


@pytest.mark.asyncio
async def test_materials_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/materials")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "ok"
        assert len(json_data["data"]) >= 20


@pytest.mark.asyncio
async def test_analytics_overview_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/analytics/overview")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "ok"
        assert "summary" in json_data["data"]


@pytest.mark.asyncio
async def test_analytics_ward_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/analytics/ward/WD-DEMO-B")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "ok"
        assert json_data["data"]["ward_id"] == "WD-DEMO-B"
        assert len(json_data["data"]["timeseries"]) >= 1


@pytest.mark.asyncio
async def test_classify_real_image_returns_a_real_classification():
    """An uploaded photo is answered by the ONNX model, not a simulator."""
    import io
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (320, 240), (60, 140, 60)).save(buf, format="JPEG")
    fake_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "input_type": "image",
        "image_b64": fake_img,
        "consent": {"image_upload": False, "analytics": True, "location": False}
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=payload)
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "ok"

        predicted = json_data["data"]["predicted_class"]
        # Either a real model class or an honest low-confidence "unknown" —
        # never a simulated material id from the removed demo pool.
        assert predicted in BROAD_CLASSES or predicted == "unknown"
        assert predicted not in ("plastic_pet_bottle", "e_waste_mobile_charger", "composite_tetrapack")

        assert 0.0 <= json_data["data"]["confidence"] <= 1.0
        assert json_data["data"]["confidence_label"] in ("high", "medium", "low")
        assert len(json_data["data"]["top3"]) == 3
        assert "bin_label" in json_data["data"]["guidance"]
        assert "demo_mode" not in json_data["meta"]
        assert json_data["meta"]["model_version"] == "yolo26n-cls-v1"


@pytest.mark.asyncio
async def test_classify_unsupported_upload_is_rejected():
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "input_type": "image",
        "image_b64": base64.b64encode(b"GIF89a" + b"\x00" * 32).decode("utf-8"),
        "consent": {"image_upload": False, "analytics": True, "location": False}
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=payload)
        assert res.status_code == 415
        assert res.json()["error"]["code"] == "UNSUPPORTED_FORMAT"

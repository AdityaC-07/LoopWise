import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "ok"
        assert json_data["data"]["demo_mode"] is True
        assert json_data["data"]["components"]["inference_engine"] == "mock"


@pytest.mark.asyncio
async def test_classify_text_description():
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "input_type": "text",
        "description": "cardboard pizza packaging box",
        "consent": {"image_upload": False, "analytics": True, "location": False}
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=payload)
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "ok"
        assert json_data["data"]["predicted_class"] is not None
        assert "bin_label" in json_data["data"]["guidance"]


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
async def test_classify_image_only_returns_unknown_demo():
    import base64
    session_id = str(uuid.uuid4())
    # Use minimal valid JPEG magic bytes
    fake_img = base64.b64encode(b'\xFF\xD8\xFF\xE0\x00\x10JFIF').decode("utf-8")
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
        assert json_data["data"]["predicted_class"] == "unknown"
        assert json_data["data"]["predicted_class"] != "e_waste_mobile_charger"
        assert json_data["data"]["confidence_label"] == "low"
        assert json_data["meta"]["demo_mode"] is True


@pytest.mark.asyncio
async def test_classify_plastic_bottle_text_returns_plastic():
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "input_type": "text",
        "description": "plastic water bottle",
        "consent": {"image_upload": False, "analytics": True, "location": False}
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/classify", json=payload)
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["data"]["predicted_class"] == "plastic_pet_bottle"

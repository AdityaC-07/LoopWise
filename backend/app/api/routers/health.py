import logging
from fastapi import APIRouter
from app.core.config import get_settings
from app.core.errors import InferenceConfigurationError
from app.core.response import build_response_envelope
from app.models.database import check_db_connection
from app.services.inference.factory import get_classifier
from app.services.storage import get_storage_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint evaluating DB, Redis, inference engine, and image store.

    ``inference_engine`` reflects whether the ONNX classifier actually loaded —
    it is never a hardcoded value. If the model failed to load, the endpoint
    reports "unavailable" and the overall status is "degraded".
    """
    db_ok = await check_db_connection()
    db_status = "ok" if db_ok else "unreachable"

    classifier = None
    inference_error = None
    try:
        classifier = get_classifier()
        inference_status = "ok"
    except InferenceConfigurationError as exc:
        inference_status = "unavailable"
        inference_error = exc.message

    # Redis check
    cache_status = "ok"
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        r.ping()
    except Exception:
        cache_status = "unreachable"

    storage_service = get_storage_service()
    storage_status = "ok" if storage_service.is_configured else "unconfigured"

    model_version = classifier.model_version if classifier else settings.MODEL_VERSION
    health_data = {
        "status": "ok" if inference_status == "ok" else "degraded",
        "components": {
            "database": db_status,
            "inference_engine": inference_status,
            "cache": cache_status,
            "image_store": storage_status
        },
        "model_version": model_version
    }
    if inference_error:
        health_data["inference_error"] = inference_error

    return build_response_envelope(
        status="ok" if inference_status == "ok" else "degraded",
        data=health_data,
        model_version=model_version
    )

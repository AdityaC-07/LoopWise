import uuid
from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse
from app.core.config import get_settings

settings = get_settings()


def build_response_envelope(
    status: str = "ok",
    data: Optional[Any] = None,
    error: Optional[Dict[str, str]] = None,
    model_version: str = "mock-v1",
    demo_mode: Optional[bool] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Constructs the standard LoopWise API response envelope."""
    return {
        "status": status,
        "data": data,
        "error": error,
        "meta": {
            "request_id": request_id or str(uuid.uuid4()),
            "model_version": model_version,
            "demo_mode": demo_mode if demo_mode is not None else settings.DEMO_MODE
        }
    }


def success_response(
    data: Any,
    model_version: str = "mock-v1",
    demo_mode: Optional[bool] = None,
    status_code: int = 200
) -> JSONResponse:
    """Returns an HTTP 200 OK JSONResponse with envelope."""
    payload = build_response_envelope(
        status="ok",
        data=data,
        error=None,
        model_version=model_version,
        demo_mode=demo_mode
    )
    return JSONResponse(content=payload, status_code=status_code)


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    model_version: str = "mock-v1"
) -> JSONResponse:
    """Returns an error JSONResponse with envelope."""
    payload = build_response_envelope(
        status="error",
        data=None,
        error={"code": code, "message": message},
        model_version=model_version
    )
    return JSONResponse(content=payload, status_code=status_code)

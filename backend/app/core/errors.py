from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.response import error_response


class LoopWiseException(Exception):
    """Base exception for LoopWise domain errors."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidInputError(LoopWiseException):
    def __init__(self, message: str = "Please add a photo or describe the item before submitting."):
        super().__init__(code="INVALID_INPUT", message=message, status_code=422)


class ImageTooLargeError(LoopWiseException):
    def __init__(self, message: str = "That photo is too large. Please try a smaller photo."):
        super().__init__(code="IMAGE_TOO_LARGE", message=message, status_code=413)


class UnsupportedFormatError(LoopWiseException):
    def __init__(self, message: str = "We couldn't read that file. Please use a JPEG or PNG photo."):
        super().__init__(code="UNSUPPORTED_FORMAT", message=message, status_code=415)


class InferenceFailedError(LoopWiseException):
    def __init__(self, message: str = "We couldn't identify this item. Try a clearer photo or describe it instead."):
        super().__init__(code="INFERENCE_FAILED", message=message, status_code=500)


class WardUnknownError(LoopWiseException):
    def __init__(self, message: str = "We don't recognise that ward. Please choose a ward from the list."):
        super().__init__(code="WARD_UNKNOWN", message=message, status_code=422)


class EventNotFoundError(LoopWiseException):
    def __init__(self, message: str = "The requested classification event was not found."):
        super().__init__(code="EVENT_NOT_FOUND", message=message, status_code=404)


class SessionMismatchError(LoopWiseException):
    def __init__(self, message: str = "Session mismatch. Please retry with your current session."):
        super().__init__(code="SESSION_MISMATCH", message=message, status_code=403)


class InvalidCorrectionError(LoopWiseException):
    def __init__(self, message: str = "We couldn't save that correction. Please try selecting a different option."):
        super().__init__(code="INVALID_CORRECTION", message=message, status_code=422)


class RateLimitedError(LoopWiseException):
    def __init__(self, message: str = "You've submitted several corrections recently. Please wait a few minutes."):
        super().__init__(code="RATE_LIMITED", message=message, status_code=429)


async def loopwise_exception_handler(request: Request, exc: LoopWiseException):
    return error_response(code=exc.code, message=exc.message, status_code=exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Plain language fallback for Pydantic validation errors
    msg = "Please add a photo or describe the item before submitting."
    errors = exc.errors()
    if errors:
        first_err = errors[0]
        field = first_err.get("loc", [])[-1] if first_err.get("loc") else ""
        if field == "image_b64":
            msg = "That photo file appears invalid. Please use a JPEG or PNG photo."
        elif field == "ward_id":
            msg = "We don't recognise that ward. Please choose a ward from the list."
        elif field == "corrected_class":
            msg = "We couldn't save that correction. Please try selecting a different option."
    return error_response(code="INVALID_INPUT", message=msg, status_code=422)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return error_response(code="NOT_FOUND", message="The requested page or endpoint was not found.", status_code=404)
    if exc.status_code == 429:
        return error_response(code="RATE_LIMITED", message="You've submitted several corrections recently. Please wait a few minutes.", status_code=429)
    return error_response(code="HTTP_ERROR", message=str(exc.detail), status_code=exc.status_code)


async def unhandled_exception_handler(request: Request, exc: Exception):
    return error_response(
        code="INFERENCE_FAILED",
        message="We couldn't connect or process your request. Please check your internet and try again.",
        status_code=500
    )

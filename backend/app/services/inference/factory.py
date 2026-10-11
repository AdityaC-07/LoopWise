import os
import logging
from app.core.config import get_settings
from app.services.inference.base import BaseClassifier
from app.services.inference.mock import MockClassifier

logger = logging.getLogger(__name__)
settings = get_settings()

_FALLBACK_TO_MOCK = False


def get_classifier() -> BaseClassifier:
    """Factory function returning the active waste classifier."""
    global _FALLBACK_TO_MOCK

    if settings.DEMO_MODE or _FALLBACK_TO_MOCK:
        logger.info("Using MockClassifier (DEMO_MODE=True or fallback active).")
        return MockClassifier()

    if not settings.MODEL_PATH or not os.path.exists(settings.MODEL_PATH):
        logger.warning(
            f"MODEL_PATH '{settings.MODEL_PATH}' not found. Falling back to MockClassifier."
        )
        _FALLBACK_TO_MOCK = True
        return MockClassifier()

    try:
        from app.services.inference.onnx_classifier import ONNXClassifier
        return ONNXClassifier(
            model_path=settings.MODEL_PATH,
            class_index_map=settings.CLASS_INDEX_MAP,
            output_semantics=getattr(settings, "MODEL_OUTPUT", None),
        )
    except Exception as e:
        logger.error(f"Failed to initialize ONNXClassifier: {e}. Falling back to MockClassifier.")
        _FALLBACK_TO_MOCK = True
        return MockClassifier()

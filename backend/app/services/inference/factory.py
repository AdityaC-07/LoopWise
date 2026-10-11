import logging
from app.core.config import get_settings
from app.core.errors import InferenceConfigurationError
from app.services.inference.base import BaseClassifier
from app.services.inference.mock import MockClassifier

logger = logging.getLogger(__name__)
settings = get_settings()

def get_classifier() -> BaseClassifier:
    """Factory function returning the active waste classifier."""
    if settings.DEMO_MODE:
        logger.info("Using MockClassifier because DEMO_MODE=True.")
        return MockClassifier()

    if not settings.MODEL_PATH:
        raise InferenceConfigurationError(
            "DEMO_MODE is false but MODEL_PATH is not set. Configure the ONNX model path or enable demo mode."
        )
    if not settings.CLASS_INDEX_MAP:
        raise InferenceConfigurationError(
            "DEMO_MODE is false but CLASS_INDEX_MAP is not set. Configure the model class map."
        )

    try:
        from app.services.inference.onnx_classifier import ONNXClassifier
        classifier = ONNXClassifier(
            model_path=settings.MODEL_PATH,
            class_index_map=settings.CLASS_INDEX_MAP,
            output_semantics=getattr(settings, "MODEL_OUTPUT", None),
        )
        if len(classifier._index_to_class) == 0:
            raise InferenceConfigurationError(
                f"CLASS_INDEX_MAP '{settings.CLASS_INDEX_MAP}' contains no usable class mappings."
            )
        return classifier
    except Exception as e:
        if isinstance(e, InferenceConfigurationError):
            raise
        logger.error("Failed to initialize ONNXClassifier: %s", e)
        raise InferenceConfigurationError(
            f"Could not load the configured ONNX model. Check MODEL_PATH and CLASS_INDEX_MAP. Details: {e}"
        ) from e

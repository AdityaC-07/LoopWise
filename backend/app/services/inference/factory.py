import logging
import threading

from app.core.config import get_settings
from app.core.errors import InferenceConfigurationError
from app.services.inference.base import BaseClassifier

logger = logging.getLogger(__name__)
settings = get_settings()

# The classifier is loaded once and reused: an ONNX session is expensive to
# build and must be identical for every request, otherwise "is the model
# ready?" has no stable answer.
_classifier: BaseClassifier | None = None
_classifier_lock = threading.Lock()


def get_classifier() -> BaseClassifier:
    """Return the application's single waste classifier.

    There is no demo or mock fallback: if the ONNX model, class-index map or
    runtime cannot be loaded, this raises InferenceConfigurationError and the
    caller surfaces an explicit service error. A result is never fabricated.
    """
    global _classifier
    if _classifier is not None:
        return _classifier

    with _classifier_lock:
        if _classifier is not None:
            return _classifier

        if not settings.MODEL_PATH:
            raise InferenceConfigurationError(
                "Image classification is not configured. Set MODEL_PATH to the ONNX model file."
            )
        if not settings.CLASS_INDEX_MAP:
            raise InferenceConfigurationError(
                "Image classification is not configured. Set CLASS_INDEX_MAP to the model class map."
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
                    "Image classification is not configured. The configured class map contains no usable class mappings."
                )
        except InferenceConfigurationError:
            raise
        except Exception as e:
            logger.error("Failed to initialize the ONNX classifier: %s", e)
            raise InferenceConfigurationError(
                "Image classification is temporarily unavailable. Please check the server and try again."
            ) from e

        _classifier = classifier
        logger.info(
            "Loaded ONNX classifier (%s) with %d classes.",
            classifier.model_version, len(classifier._index_to_class),
        )
        return _classifier


def reset_classifier_cache() -> None:
    """Drop the cached classifier (used by tests to force a fresh load)."""
    global _classifier
    with _classifier_lock:
        _classifier = None

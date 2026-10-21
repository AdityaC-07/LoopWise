from abc import ABC, abstractmethod
from typing import Optional
from app.services.inference.result import ClassificationResult


class BaseClassifier(ABC):
    """Abstract Base Class for Waste Classifiers."""
    
    @property
    @abstractmethod
    def model_version(self) -> str:
        """Returns the version string of the model."""
        pass

    @abstractmethod
    async def classify(
        self,
        image_bytes: Optional[bytes] = None,
        description: Optional[str] = None
    ) -> ClassificationResult:
        """Classifies a waste item from uploaded image bytes.

        The description is optional extra context; image bytes carry the
        classification. Implementations must never fabricate a result when the
        model is unavailable — they raise instead.
        """
        pass

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

    @property
    @abstractmethod
    def is_demo(self) -> bool:
        """Returns True if the classifier runs in demo/mock mode."""
        pass

    @abstractmethod
    async def classify(
        self,
        image_bytes: Optional[bytes] = None,
        description: Optional[str] = None
    ) -> ClassificationResult:
        """Classifies a waste item based on image bytes or text description."""
        pass

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


# Repository-relative location of the approved V1 classifier artefacts. Used as
# the default so a local checkout runs with no .env; deployments override both
# via environment variables.
_REPO_MODELS_DIR = Path(__file__).resolve().parents[3] / "ml" / "models"
DEFAULT_MODEL_PATH = str(_REPO_MODELS_DIR / "loopwise-yolo26n-cls.onnx")
DEFAULT_CLASS_INDEX_MAP = str(_REPO_MODELS_DIR / "loopwise-yolo26n-cls.class-index-map.json")


class Settings(BaseSettings):
    """LoopWise Application Settings loaded from environment or defaults."""

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Data Stores
    DATABASE_URL: str = "sqlite+aiosqlite:///./loopwise.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ML & Storage
    MODEL_PATH: str | None = DEFAULT_MODEL_PATH
    CLASS_INDEX_MAP: str | None = DEFAULT_CLASS_INDEX_MAP
    MODEL_VERSION: str = "yolo26n-cls-v1"
    # ONNX output semantics. The exported yolov8/26-cls head already contains
    # Softmax, so its output is a probability distribution -> "probabilities"
    # (default). A model that returns raw logits MUST opt in with "logits";
    # the classifier never guesses and never applies softmax twice.
    MODEL_OUTPUT: Literal["probabilities", "logits"] = "probabilities"
    S3_BUCKET: str | None = None
    AWS_REGION: str = "ap-south-1"

    # Security & Auth
    SECRET_KEY: str = "loopwise-development-secret-key-32-chars-minimum!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()

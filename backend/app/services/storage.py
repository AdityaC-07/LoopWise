import logging
from typing import Optional, Tuple
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageService:
    """Optional Amazon S3 storage service for consent-gated image uploads."""

    def __init__(self):
        self.bucket_name = settings.S3_BUCKET
        self.region = settings.AWS_REGION

    @property
    def is_configured(self) -> bool:
        return bool(self.bucket_name)

    async def store_image_if_consented(
        self,
        event_id: str,
        image_bytes: Optional[bytes],
        consent_image_upload: bool
    ) -> Tuple[bool, Optional[str]]:
        """Stores image to S3 ONLY if explicitly consented by user and S3 is configured.
        
        Returns (image_stored: bool, image_key: Optional[str]).
        """
        # Strict privacy enforcement: never store without explicit per-event consent
        if not consent_image_upload or not image_bytes:
            return False, None

        if not self.is_configured:
            logger.info("Image upload consented, but S3_BUCKET is not configured. Image discarded.")
            return False, None

        try:
            import boto3
            s3_client = boto3.client("s3", region_name=self.region)
            key = f"events/{event_id}/waste_item.jpg"
            
            s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_bytes,
                ContentType="image/jpeg",
                ServerSideEncryption="AES256"
            )
            logger.info(f"Consented image successfully stored to S3: {key}")
            return True, key
        except Exception as e:
            logger.error(f"Failed to store image to S3: {e}")
            return False, None


_storage_service = StorageService()


def get_storage_service() -> StorageService:
    return _storage_service

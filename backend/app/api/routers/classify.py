import base64
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.response import success_response
from app.core.errors import WardUnknownError
from app.api.schemas.classify import ClassifyRequest, ClassifyResponseData
from app.models.database import get_db, check_db_connection
from app.models.events import ClassificationEvent, InputTypeEnum
from app.services.inference.factory import get_classifier
from app.services.storage import get_storage_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Classification"])

VALID_WARDS = {"WD-DEMO-A", "WD-DEMO-B", "WD-DEMO-C", "WD-001", "WD-002", "WD-003"}


@router.post("/classify")
async def classify_item(
    payload: ClassifyRequest,
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Classifies a waste item from an uploaded photo and provides disposal guidance."""
    # Ward ID validation if provided
    if payload.ward_id and payload.ward_id not in VALID_WARDS:
        raise WardUnknownError(f"We don't recognise ward '{payload.ward_id}'. Please choose a valid ward.")

    # Decode image bytes in memory
    image_bytes: Optional[bytes] = None
    if payload.image_b64:
        raw_b64 = payload.image_b64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        image_bytes = base64.b64decode(raw_b64)

    # Execute classification
    classifier = get_classifier()
    result = await classifier.classify(
        image_bytes=image_bytes,
        description=payload.description
    )

    # Privacy & Storage: Store image ONLY if explicitly consented by user
    storage_service = get_storage_service()
    image_stored, image_key = await storage_service.store_image_if_consented(
        event_id=result.event_id,
        image_bytes=image_bytes,
        consent_image_upload=payload.consent.image_upload
    )

    # Try saving classification event to DB (fail gracefully if DB unavailable)
    db_connected = await check_db_connection()
    if db_connected and db is not None:
        try:
            event = ClassificationEvent(
                event_id=str(result.event_id),
                session_id=str(payload.session_id),
                user_id=None,
                ward_id=payload.ward_id,
                input_type=InputTypeEnum.image if payload.image_b64 else InputTypeEnum.text,
                model_version=result.model_version,
                predicted_class=result.predicted_class,
                confidence=result.confidence,
                top3_predictions=result.top3,
                material_category=result.material.category,
                disposal_bin=result.material.disposal_bin,
                recovery_potential=result.material.recovery_potential,
                recovery_channel=result.material.recovery_channel,
                is_corrected=False,
                correction_id=None,
                image_stored=image_stored,
                image_key=image_key,
                consent_flags=payload.consent.model_dump(),
            )
            db.add(event)
            await db.commit()
        except Exception as e:
            logger.warning(f"Could not persist ClassificationEvent to DB: {e}")
            await db.rollback()

    response_data = {
        "event_id": result.event_id,
        "predicted_class": result.predicted_class,
        "confidence": result.confidence,
        "confidence_label": result.confidence_label,
        "top3": result.top3,
        "material": {
            "name": result.material.name,
            "category": result.material.category,
            "disposal_bin": result.material.disposal_bin,
            "recovery_potential": result.material.recovery_potential,
            "next_life": result.material.next_life,
            "recovery_channel": result.material.recovery_channel,
            "contamination_notes": result.material.contamination_notes
        },
        "guidance": {
            "bin_label": result.guidance.bin_label,
            "action": result.guidance.action,
            "do": result.guidance.do,
            "do_not": result.guidance.do_not
        }
    }

    return success_response(
        data=response_data,
        model_version=result.model_version
    )

import time
import uuid
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.response import success_response
from app.core.errors import RateLimitedError, EventNotFoundError, SessionMismatchError, InvalidCorrectionError
from app.api.schemas.feedback import FeedbackRequest, FeedbackResponseData
from app.models.database import get_db, check_db_connection
from app.models.events import ClassificationEvent
from app.models.corrections import UserCorrection

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Feedback"])

# In-memory rate limiting fallback if Redis is unreachable
_MEMORY_RATE_LIMITS: Dict[str, List[float]] = {}


def check_rate_limit(session_id: str, limit: int = 10, window_seconds: int = 3600):
    """Enforces max 10 feedback submissions per session per hour."""
    now = time.time()
    
    # Try Redis first
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        key = f"rate_limit:feedback:{session_id}"
        current = r.incr(key)
        if current == 1:
            r.expire(key, window_seconds)
        if current > limit:
            raise RateLimitedError()
        return
    except RateLimitedError:
        raise
    except Exception:
        pass  # Fall back to in-memory rate limiting

    # In-memory fallback
    timestamps = _MEMORY_RATE_LIMITS.get(session_id, [])
    timestamps = [t for t in timestamps if now - t < window_seconds]
    if len(timestamps) >= limit:
        raise RateLimitedError()
    timestamps.append(now)
    _MEMORY_RATE_LIMITS[session_id] = timestamps


@router.post("/feedback")
async def submit_feedback(
    payload: FeedbackRequest,
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Submits user correction or confirmation feedback for a prediction."""
    # Enforce rate limiting
    check_rate_limit(str(payload.session_id))

    correction_id = str(uuid.uuid4())
    db_connected = await check_db_connection()

    if db_connected and db is not None:
        try:
            # Check event exists
            stmt = select(ClassificationEvent).where(ClassificationEvent.event_id == str(payload.event_id))
            res = await db.execute(stmt)
            event = res.scalar_one_or_none()

            if event:
                if str(event.session_id) != str(payload.session_id):
                    raise SessionMismatchError()

                if payload.feedback_type == "correction":
                    correction = UserCorrection(
                        correction_id=correction_id,
                        event_id=str(payload.event_id),
                        session_id=str(payload.session_id),
                        user_id=None,
                        corrected_class=payload.corrected_class,
                        correction_note=payload.note,
                        reviewed=False  # Unverified feedback — requires human review before retraining
                    )
                    db.add(correction)
                    event.is_corrected = True
                    event.correction_id = correction_id
                    await db.commit()
            else:
                logger.info(f"Event '{payload.event_id}' not in DB (mock/memory event). Feedback acknowledged.")
        except (SessionMismatchError, RateLimitedError):
            raise
        except Exception as e:
            logger.warning(f"Error persisting feedback to DB: {e}")
            await db.rollback()

    response_data = {
        "correction_id": str(correction_id) if payload.feedback_type == "correction" else None,
        "acknowledged": True
    }

    return success_response(data=response_data)

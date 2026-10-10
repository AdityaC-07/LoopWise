import datetime
import logging
from typing import Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import ClassificationEvent, RecoveryPotentialEnum
from app.models.corrections import UserCorrection
from app.models.analytics import WardAnalyticsRollup

logger = logging.getLogger(__name__)


async def compute_ward_rollup(db: AsyncSession, ward_id: str, date: datetime.date) -> Optional[WardAnalyticsRollup]:
    """Computes daily analytics rollup for a given ward and date."""
    start_dt = datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc)
    end_dt = datetime.datetime.combine(date, datetime.time.max, tzinfo=datetime.timezone.utc)

    # Filter out demo_mode = true events for production aggregation
    stmt = select(ClassificationEvent).where(
        ClassificationEvent.ward_id == ward_id,
        ClassificationEvent.created_at >= start_dt,
        ClassificationEvent.created_at <= end_dt,
        ClassificationEvent.demo_mode == False
    )
    res = await db.execute(stmt)
    events = res.scalars().all()

    if not events:
        logger.info(f"No non-demo events found for ward '{ward_id}' on {date}.")
        return None

    total_events = len(events)
    unique_sessions = len(set(e.session_id for e in events))
    
    corrected_count = sum(1 for e in events if e.is_corrected)
    correction_rate = round(corrected_count / total_events, 4)

    # Contamination rate = proportion of items with low or no recovery potential (wrongly sorted)
    contam_count = sum(1 for e in events if e.recovery_potential in (RecoveryPotentialEnum.low, RecoveryPotentialEnum.none))
    contamination_rate = round(contam_count / total_events, 4)

    # Recovery potential normalized (high=1.0, medium=0.6, low=0.2, none=0.0)
    rec_map = {
        RecoveryPotentialEnum.high: 1.0,
        RecoveryPotentialEnum.medium: 0.6,
        RecoveryPotentialEnum.low: 0.2,
        RecoveryPotentialEnum.none: 0.0
    }
    rec_sum = sum(rec_map.get(e.recovery_potential, 0.0) for e in events)
    recovery_potential_avg = round(rec_sum / total_events, 4)

    # Low confidence rate (confidence < 0.55)
    low_conf_count = sum(1 for e in events if e.confidence < 0.55)
    low_confidence_rate = round(low_conf_count / total_events, 4)

    # Material breakdown
    mat_counts: Dict[str, int] = {}
    for e in events:
        cat = e.material_category.value if hasattr(e.material_category, "value") else str(e.material_category)
        mat_counts[cat] = mat_counts.get(cat, 0) + 1
    
    material_breakdown = {cat: round(cnt / total_events, 4) for cat, cnt in mat_counts.items()}

    # Misclassifications
    corr_stmt = select(ClassificationEvent.predicted_class, UserCorrection.corrected_class, func.count())\
        .join(UserCorrection, ClassificationEvent.correction_id == UserCorrection.correction_id)\
        .where(
            ClassificationEvent.ward_id == ward_id,
            ClassificationEvent.created_at >= start_dt,
            ClassificationEvent.created_at <= end_dt,
            ClassificationEvent.demo_mode == False
        )\
        .group_by(ClassificationEvent.predicted_class, UserCorrection.corrected_class)
    
    corr_res = await db.execute(corr_stmt)
    top_misclassifications = [
        {"predicted": row[0], "corrected": row[1], "count": row[2]}
        for row in corr_res.all()
    ]

    # Upsert rollup
    existing_stmt = select(WardAnalyticsRollup).where(
        WardAnalyticsRollup.ward_id == ward_id,
        WardAnalyticsRollup.date == date
    )
    existing_res = await db.execute(existing_stmt)
    rollup = existing_res.scalar_one_or_none()

    if not rollup:
        rollup = WardAnalyticsRollup(
            ward_id=ward_id,
            date=date,
            total_events=total_events,
            unique_sessions=unique_sessions,
            correction_rate=correction_rate,
            contamination_rate=contamination_rate,
            recovery_potential_avg=recovery_potential_avg,
            low_confidence_rate=low_confidence_rate,
            material_breakdown=material_breakdown,
            top_misclassifications=top_misclassifications
        )
        db.add(rollup)
    else:
        rollup.total_events = total_events
        rollup.unique_sessions = unique_sessions
        rollup.correction_rate = correction_rate
        rollup.contamination_rate = contamination_rate
        rollup.recovery_potential_avg = recovery_potential_avg
        rollup.low_confidence_rate = low_confidence_rate
        rollup.material_breakdown = material_breakdown
        rollup.top_misclassifications = top_misclassifications
        rollup.computed_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()
    return rollup

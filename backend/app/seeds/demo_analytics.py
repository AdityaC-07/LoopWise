import asyncio
import datetime
import logging
from typing import List, Dict, Any
from sqlalchemy import select
from app.models.database import AsyncSessionLocal, check_db_connection
from app.models.analytics import WardAnalyticsRollup

logger = logging.getLogger(__name__)


def generate_demo_rollups() -> List[Dict[str, Any]]:
    """Generates 30 days of synthetic ward analytics rollups for 3 demo wards."""
    today = datetime.date.today()
    rollups = []

    for day_offset in range(29, -1, -1):
        target_date = today - datetime.timedelta(days=day_offset)
        day_index = 30 - day_offset  # 1 to 30

        # Ward A: Improving contamination trend
        # contamination drops from ~0.34 down to ~0.10
        ward_a_contam = max(0.10, 0.35 - (day_index * 0.008))
        ward_a_recovery = min(0.85, 0.60 + (day_index * 0.008))
        rollups.append({
            "ward_id": "WD-DEMO-A",
            "date": target_date,
            "total_events": 45 + (day_index % 7) * 3,
            "unique_sessions": 30 + (day_index % 5) * 2,
            "correction_rate": round(max(0.05, 0.20 - day_index * 0.004), 2),
            "contamination_rate": round(ward_a_contam, 2),
            "recovery_potential_avg": round(ward_a_recovery, 2),
            "low_confidence_rate": round(max(0.04, 0.15 - day_index * 0.003), 2),
            "material_breakdown": {"plastic": 0.40, "paper": 0.25, "organic": 0.20, "glass": 0.08, "metal": 0.07},
            "top_misclassifications": [
                {"predicted": "composite_tetrapack", "corrected": "plastic_pet_bottle", "count": 12},
                {"predicted": "plastic_ldpe_bag", "corrected": "plastic_hdpe_container", "count": 8}
            ]
        })

        # Ward B: Contamination spike on days 14–18
        if 14 <= day_index <= 18:
            ward_b_contam = 0.48
            ward_b_recovery = 0.42
            ward_b_corr = 0.31
        else:
            ward_b_contam = 0.18
            ward_b_recovery = 0.76
            ward_b_corr = 0.11

        rollups.append({
            "ward_id": "WD-DEMO-B",
            "date": target_date,
            "total_events": 60 + (day_index % 6) * 4,
            "unique_sessions": 40 + (day_index % 4) * 3,
            "correction_rate": round(ward_b_corr, 2),
            "contamination_rate": round(ward_b_contam, 2),
            "recovery_potential_avg": round(ward_b_recovery, 2),
            "low_confidence_rate": round(0.12 if 14 <= day_index <= 18 else 0.07, 2),
            "material_breakdown": {"plastic": 0.35, "paper": 0.20, "organic": 0.30, "glass": 0.08, "metal": 0.07},
            "top_misclassifications": [
                {"predicted": "organic_food_waste", "corrected": "paper_soiled_napkin", "count": 24 if 14 <= day_index <= 18 else 5},
                {"predicted": "composite_tetrapack", "corrected": "paper_cardboard_box", "count": 14}
            ]
        })

        # Ward C: Consistently high recovery potential
        rollups.append({
            "ward_id": "WD-DEMO-C",
            "date": target_date,
            "total_events": 75 + (day_index % 8) * 2,
            "unique_sessions": 50 + (day_index % 5) * 4,
            "correction_rate": round(0.08 + (day_index % 3) * 0.01, 2),
            "contamination_rate": round(0.09 + (day_index % 4) * 0.01, 2),
            "recovery_potential_avg": round(0.86 + (day_index % 3) * 0.01, 2),
            "low_confidence_rate": round(0.05, 2),
            "material_breakdown": {"plastic": 0.38, "paper": 0.30, "organic": 0.18, "glass": 0.08, "metal": 0.06},
            "top_misclassifications": [
                {"predicted": "metal_can_aluminum", "corrected": "hazardous_battery_aa", "count": 3}
            ]
        })

    return rollups


async def seed_demo_analytics_database():
    """Seeds 30 days of synthetic rollups into database if connected."""
    if not await check_db_connection():
        logger.warning("Database not connected. Skipping DB analytics seed insertion.")
        return

    rollups = generate_demo_rollups()
    async with AsyncSessionLocal() as session:
        try:
            inserted_count = 0
            for r_data in rollups:
                stmt = select(WardAnalyticsRollup).where(
                    WardAnalyticsRollup.ward_id == r_data["ward_id"],
                    WardAnalyticsRollup.date == r_data["date"]
                )
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()
                if not existing:
                    rollup = WardAnalyticsRollup(**r_data)
                    session.add(rollup)
                    inserted_count += 1
            await session.commit()
            logger.info(f"Successfully seeded {inserted_count} analytics rollups into DB.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error seeding demo analytics: {e}")


def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_demo_analytics_database())


if __name__ == "__main__":
    main()

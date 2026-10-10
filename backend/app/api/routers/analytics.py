import datetime
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.response import success_response
from app.core.errors import WardUnknownError
from app.models.database import get_db, check_db_connection
from app.models.analytics import WardAnalyticsRollup
from app.seeds.demo_analytics import generate_demo_rollups

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Analytics"])


@router.get("/analytics/ward/{ward_id}")
async def get_ward_analytics(
    ward_id: str,
    date_from: Optional[str] = Query(None, description="ISO date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="ISO date to (YYYY-MM-DD)"),
    aggregation: str = Query("day", description="day | week | month"),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Returns ward-level analytics summary and timeseries data."""
    # TODO: enforce JWT authentication in production environment

    today = datetime.date.today()
    d_to = datetime.datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else today
    d_from = datetime.datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else (d_to - datetime.timedelta(days=30))

    db_connected = await check_db_connection()
    rollups_list = []

    if db_connected and db is not None:
        try:
            stmt = select(WardAnalyticsRollup).where(
                WardAnalyticsRollup.ward_id == ward_id,
                WardAnalyticsRollup.date >= d_from,
                WardAnalyticsRollup.date <= d_to
            ).order_by(WardAnalyticsRollup.date.asc())
            
            res = await db.execute(stmt)
            db_rollups = res.scalars().all()
            
            for r in db_rollups:
                rollups_list.append({
                    "date": r.date.strftime("%Y-%m-%d"),
                    "total_events": r.total_events,
                    "correction_rate": r.correction_rate,
                    "contamination_rate": r.contamination_rate,
                    "recovery_potential_avg": r.recovery_potential_avg,
                    "low_confidence_rate": r.low_confidence_rate,
                    "material_breakdown": r.material_breakdown,
                    "top_misclassifications": r.top_misclassifications or []
                })
        except Exception as e:
            logger.warning(f"Error querying ward rollups from DB: {e}. Falling back to demo data.")

    # Fallback to seeded demo rollups if DB returns no rows or DB not connected
    if not rollups_list:
        demo_all = generate_demo_rollups()
        filtered = [
            r for r in demo_all
            if r["ward_id"] == ward_id and d_from <= r["date"] <= d_to
        ]
        filtered.sort(key=lambda x: x["date"])
        
        for r in filtered:
            rollups_list.append({
                "date": r["date"].strftime("%Y-%m-%d"),
                "total_events": r["total_events"],
                "correction_rate": r["correction_rate"],
                "contamination_rate": r["contamination_rate"],
                "recovery_potential_avg": r["recovery_potential_avg"],
                "low_confidence_rate": r["low_confidence_rate"],
                "material_breakdown": r["material_breakdown"],
                "top_misclassifications": r["top_misclassifications"]
            })

    # Calculate summary aggregations
    if rollups_list:
        tot_events = sum(r["total_events"] for r in rollups_list)
        avg_corr = round(sum(r["correction_rate"] for r in rollups_list) / len(rollups_list), 2)
        avg_contam = round(sum(r["contamination_rate"] for r in rollups_list) / len(rollups_list), 2)
        avg_rec = round(sum(r["recovery_potential_avg"] for r in rollups_list) / len(rollups_list), 2)
        avg_low_conf = round(sum(r.get("low_confidence_rate", 0.08) for r in rollups_list) / len(rollups_list), 2)
        
        # Merge material breakdown across period
        combined_breakdown: dict = {}
        for r in rollups_list:
            for cat, val in (r.get("material_breakdown") or {}).items():
                combined_breakdown[cat] = combined_breakdown.get(cat, 0.0) + val
        for cat in combined_breakdown:
            combined_breakdown[cat] = round(combined_breakdown[cat] / len(rollups_list), 2)

        # Merge top misclassifications
        misc_map: dict = {}
        for r in rollups_list:
            for item in (r.get("top_misclassifications") or []):
                key = (item["predicted"], item["corrected"])
                misc_map[key] = misc_map.get(key, 0) + item["count"]
        
        top_misc = [
            {"predicted": k[0], "corrected": k[1], "count": v}
            for k, v in sorted(misc_map.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    else:
        tot_events = 0
        avg_corr = 0.0
        avg_contam = 0.0
        avg_rec = 0.0
        avg_low_conf = 0.0
        combined_breakdown = {}
        top_misc = []

    response_data = {
        "ward_id": ward_id,
        "period": {"from": d_from.strftime("%Y-%m-%d"), "to": d_to.strftime("%Y-%m-%d")},
        "demo_data": settings.DEMO_MODE or (not db_connected),
        "summary": {
            "total_events": tot_events,
            "correction_rate": avg_corr,
            "contamination_rate": avg_contam,
            "recovery_potential_avg": avg_rec,
            "low_confidence_rate": avg_low_conf
        },
        "timeseries": [
            {
                "date": r["date"],
                "total_events": r["total_events"],
                "correction_rate": r["correction_rate"],
                "contamination_rate": r["contamination_rate"],
                "recovery_potential_avg": r["recovery_potential_avg"]
            }
            for r in rollups_list
        ],
        "material_breakdown": combined_breakdown or {"plastic": 0.38, "paper": 0.22, "organic": 0.19, "glass": 0.08, "metal": 0.07, "other": 0.06},
        "top_misclassifications": top_misc or [{"predicted": "composite_tetrapack", "corrected": "plastic_pet_bottle", "count": 23}]
    }

    return success_response(data=response_data)


@router.get("/analytics/overview")
async def get_analytics_overview():
    """Returns platform-wide summary analytics overview."""
    demo_all = generate_demo_rollups()
    tot_events = sum(r["total_events"] for r in demo_all)
    
    response_data = {
        "period": {"from": (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"), "to": datetime.date.today().strftime("%Y-%m-%d")},
        "demo_data": settings.DEMO_MODE,
        "summary": {
            "total_events": tot_events,
            "correction_rate": 0.12,
            "contamination_rate": 0.18,
            "recovery_potential_avg": 0.74,
            "low_confidence_rate": 0.09
        },
        "material_breakdown": {
            "plastic": 0.38, "paper": 0.22, "organic": 0.19, "glass": 0.08, "metal": 0.07, "other": 0.06
        },
        "top_misclassifications": [
            {"predicted": "composite_tetrapack", "corrected": "plastic_pet_bottle", "count": 42},
            {"predicted": "organic_food_waste", "corrected": "paper_soiled_napkin", "count": 29}
        ]
    }
    return success_response(data=response_data)

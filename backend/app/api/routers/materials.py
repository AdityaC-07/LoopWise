import logging
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.models.database import get_db, check_db_connection
from app.models.materials import Material
from app.seeds.materials import SEED_MATERIALS

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Materials"])


@router.get("/materials")
async def get_materials_list(db: Optional[AsyncSession] = Depends(get_db)):
    """Returns the full materials taxonomy reference list."""
    materials_list = []
    db_connected = await check_db_connection()

    if db_connected and db is not None:
        try:
            stmt = select(Material)
            res = await db.execute(stmt)
            db_mats = res.scalars().all()
            for m in db_mats:
                materials_list.append({
                    "material_id": m.material_id,
                    "name": m.name,
                    "category": m.category.value if hasattr(m.category, "value") else str(m.category),
                    "subcategory": m.subcategory,
                    "disposal_bin": m.disposal_bin.value if hasattr(m.disposal_bin, "value") else str(m.disposal_bin),
                    "recovery_potential": m.recovery_potential.value if hasattr(m.recovery_potential, "value") else str(m.recovery_potential),
                    "next_life": m.next_life,
                    "recovery_channel": m.recovery_channel,
                    "contamination_notes": m.contamination_notes,
                    "icon_slug": m.icon_slug,
                    "demo_seed": m.demo_seed
                })
        except Exception as e:
            logger.warning(f"Error reading materials from DB: {e}. Falling back to seeds.")

    if not materials_list:
        # Fallback to seed materials list for initial demo without DB
        for m in SEED_MATERIALS:
            materials_list.append({
                "material_id": m["material_id"],
                "name": m["name"],
                "category": m["category"].value if hasattr(m["category"], "value") else str(m["category"]),
                "subcategory": m["subcategory"],
                "disposal_bin": m["disposal_bin"].value if hasattr(m["disposal_bin"], "value") else str(m["disposal_bin"]),
                "recovery_potential": m["recovery_potential"].value if hasattr(m["recovery_potential"], "value") else str(m["recovery_potential"]),
                "next_life": m["next_life"],
                "recovery_channel": m["recovery_channel"],
                "contamination_notes": m["contamination_notes"],
                "icon_slug": m["icon_slug"],
                "demo_seed": m["demo_seed"]
            })

    return success_response(data=materials_list)

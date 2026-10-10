from typing import Optional
from pydantic import BaseModel


class MaterialSchema(BaseModel):
    material_id: str
    name: str
    category: str
    subcategory: Optional[str] = None
    disposal_bin: str
    recovery_potential: str
    next_life: Optional[str] = None
    recovery_channel: Optional[str] = None
    contamination_notes: Optional[str] = None
    icon_slug: Optional[str] = None
    demo_seed: bool = False

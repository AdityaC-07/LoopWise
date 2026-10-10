from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MaterialGuidance:
    name: str
    category: str
    disposal_bin: str
    recovery_potential: str
    next_life: str
    recovery_channel: str
    contamination_notes: str


@dataclass
class DisposalGuidance:
    bin_label: str
    action: str
    do: List[str]
    do_not: List[str]


@dataclass
class ClassificationResult:
    event_id: str
    predicted_class: str
    confidence: float
    confidence_label: str  # "high", "medium", "low"
    top3: List[Dict[str, Any]]  # [{"class": str, "confidence": float}]
    material: MaterialGuidance
    guidance: DisposalGuidance
    model_version: str = "mock-v1"
    is_demo: bool = True

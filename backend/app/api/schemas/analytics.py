from typing import List, Dict, Optional
from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_events: int
    correction_rate: float
    contamination_rate: float
    recovery_potential_avg: float
    low_confidence_rate: float


class TimeseriesPoint(BaseModel):
    date: str
    total_events: int
    correction_rate: float
    contamination_rate: float
    recovery_potential_avg: float


class TopMisclassification(BaseModel):
    predicted: str
    corrected: str
    count: int


class WardAnalyticsResponse(BaseModel):
    ward_id: str
    period: Dict[str, str]
    demo_data: bool
    summary: AnalyticsSummary
    timeseries: List[TimeseriesPoint]
    material_breakdown: Dict[str, float]
    top_misclassifications: List[TopMisclassification]


class OverviewResponse(BaseModel):
    period: Dict[str, str]
    demo_data: bool
    summary: AnalyticsSummary
    material_breakdown: Dict[str, float]
    top_misclassifications: List[TopMisclassification]

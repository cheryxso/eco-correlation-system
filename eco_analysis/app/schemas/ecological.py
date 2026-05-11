from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.ecological import EcoIndicatorType, EcoDataSource

class EcologicalCreate(BaseModel):
    territory_id: int
    indicator_type: EcoIndicatorType
    value: float
    unit: Optional[str] = None
    measured_at: datetime
    source: EcoDataSource = EcoDataSource.csv

class EcologicalResponse(BaseModel):
    id: int
    territory_id: int
    indicator_type: EcoIndicatorType
    value: float
    unit: Optional[str]
    measured_at: datetime
    source: EcoDataSource
    created_at: datetime

    class Config:
        from_attributes = True
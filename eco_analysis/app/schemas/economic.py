from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.economic import EconIndicatorType, EconDataSource

class EconomicCreate(BaseModel):
    territory_id: int
    indicator_type: EconIndicatorType
    value: float
    unit: Optional[str] = None
    period: str
    source: EconDataSource = EconDataSource.csv

class EconomicResponse(BaseModel):
    id: int
    territory_id: int
    indicator_type: EconIndicatorType
    value: float
    unit: Optional[str]
    period: str
    source: EconDataSource
    created_at: datetime

    class Config:
        from_attributes = True
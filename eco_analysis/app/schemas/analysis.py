from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from app.models.analysis import AnalysisMethod, AnalysisStatus

class AnalysisSessionCreate(BaseModel):
    user_id: int
    dataset_id: int
    method: AnalysisMethod
    parameters: Optional[Dict[str, Any]] = None

class AnalysisSessionResponse(BaseModel):
    id: int
    user_id: int
    dataset_id: int
    method: AnalysisMethod
    status: AnalysisStatus
    created_at: datetime

    class Config:
        from_attributes = True

class AnalysisResultResponse(BaseModel):
    id: int
    session_id: int
    indicator_x: str
    indicator_y: str
    coefficient: Optional[float]
    p_value: Optional[float]
    is_significant: Optional[bool]
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
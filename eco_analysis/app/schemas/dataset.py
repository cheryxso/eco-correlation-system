from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DatasetCreate(BaseModel):
    user_id: int
    name: str
    description: Optional[str] = None

class DatasetResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
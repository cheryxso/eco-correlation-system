from pydantic import BaseModel
from typing import Optional

class TerritoryCreate(BaseModel):
    name: str
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geojson: Optional[str] = None

class TerritoryResponse(BaseModel):
    id: int
    name: str
    region: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        from_attributes = True
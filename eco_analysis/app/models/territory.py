from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Territory(Base):
    __tablename__ = "territories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    region = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geojson = Column(Text, nullable=True)

    ecological_measurements = relationship("EcologicalMeasurement", back_populates="territory")
    economic_measurements = relationship("EconomicMeasurement", back_populates="territory")
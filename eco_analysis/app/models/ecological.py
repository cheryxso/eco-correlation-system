from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class EcoIndicatorType(str, enum.Enum):
    turbidity = "turbidity"
    pm25 = "PM2.5"
    pm10 = "PM10"
    aqi = "AQI"
    temperature = "temperature"
    humidity = "humidity"
    pressure = "pressure"

class EcoDataSource(str, enum.Enum):
    csv = "csv"
    openaq = "openaq"
    saveecobot = "saveecobot"

class EcologicalMeasurement(Base):
    __tablename__ = "ecological_measurements"

    id = Column(Integer, primary_key=True, index=True)
    territory_id = Column(Integer, ForeignKey("territories.id"), nullable=False)
    indicator_type = Column(Enum(EcoIndicatorType), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    measured_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(Enum(EcoDataSource), default=EcoDataSource.csv)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    territory = relationship("Territory", back_populates="ecological_measurements")
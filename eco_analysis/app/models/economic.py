from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class EconIndicatorType(str, enum.Enum):
    gdp = "gdp"
    salary = "salary"
    unemployment = "unemployment"
    enterprises = "enterprises"
    healthcare = "healthcare"
    investments = "investments"

class EconDataSource(str, enum.Enum):
    csv = "csv"
    manual = "manual"

class EconomicMeasurement(Base):
    __tablename__ = "economic_measurements"

    id = Column(Integer, primary_key=True, index=True)
    territory_id = Column(Integer, ForeignKey("territories.id"), nullable=False)
    indicator_type = Column(Enum(EconIndicatorType), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    period = Column(String, nullable=False)
    source = Column(Enum(EconDataSource), default=EconDataSource.csv)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    territory = relationship("Territory", back_populates="economic_measurements")
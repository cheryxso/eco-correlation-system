from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class AnalysisMethod(str, enum.Enum):
    pearson = "pearson"
    spearman = "spearman"
    kendall = "kendall"
    partial = "partial"
    timeseries = "timeseries"
    regression = "regression"
    comparison = "comparison"

class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    method = Column(Enum(AnalysisMethod), nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="analysis_sessions")
    dataset = relationship("Dataset", back_populates="analysis_sessions")
    results = relationship("AnalysisResult", back_populates="session")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id"), nullable=False)
    indicator_x = Column(String, nullable=False)
    indicator_y = Column(String, nullable=False)
    coefficient = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    is_significant = Column(Boolean, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("AnalysisSession", back_populates="results")
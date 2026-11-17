# backend/database/models.py
import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from backend.database.database import Base

class ExperimentRecordDB(Base):
    __tablename__ = "experiment_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    query = Column(Text, nullable=False)
    input_type = Column(String(32), nullable=False)
    modality = Column(String(32), nullable=False)
    detected_task = Column(String(32), nullable=False)
    selected_model = Column(String(64), nullable=True)
    routing_reasons = Column(Text, nullable=True)
    routing_latency_ms = Column(Float, default=0.0)
    model_latency_ms = Column(Float, default=0.0)
    total_latency_ms = Column(Float, default=0.0)
    status = Column(String(32), default="success")
    success = Column(Boolean, default=True)
    answer = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    compatibility_summary = Column(Text, nullable=True)
    metadata_summary = Column(Text, nullable=True)
    raw_trace_json = Column(Text, nullable=True)

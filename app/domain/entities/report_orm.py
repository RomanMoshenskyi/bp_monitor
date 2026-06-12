"""Report ORM Model - from diploma class diagram."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.infrastructure.orm.base import Base


class ReportFormat(str, enum.Enum):
    """Available report formats."""
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class ReportStatus(str, enum.Enum):
    """Report generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportORM(Base):
    """
    Report entity - from diploma class diagram.
    
    Generated reports for patients (PDF, CSV, JSON).
    
    Attributes:
        id: Primary key
        patient_id: FK to users
        period_start, period_end: Date range of report
        file_path: Path to generated file
        file_format: pdf/csv/json
        file_size: Size in bytes
        status: Generation status
        error_message: If generation failed
        generated_by: Who requested (doctor_id or patient)
    """
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Report period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # File info
    file_path = Column(String(500), nullable=True)  # Nullable until generated
    file_format = Column(Enum(ReportFormat), nullable=False)
    file_size = Column(Integer, nullable=True)  # Bytes
    
    # Status tracking
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Who generated
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Doctor or self
    generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional title/description
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = DateTime(timezone=True)
    
    # Relationships
    patient = relationship("UserORM", foreign_keys=[patient_id], back_populates="reports")
    generator = relationship("UserORM", foreign_keys=[generated_by])
    
    def __repr__(self) -> str:
        return f"<ReportORM(id={self.id}, patient_id={self.patient_id}, format={self.file_format.value}, status={self.status.value})>"
    
    def mark_completed(self, file_path: str, file_size: int) -> None:
        """Mark report as successfully generated."""
        self.status = ReportStatus.COMPLETED
        self.file_path = file_path
        self.file_size = file_size
        self.generated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str) -> None:
        """Mark report generation as failed."""
        self.status = ReportStatus.FAILED
        self.error_message = error_message
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "file_format": self.file_format.value,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

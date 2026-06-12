"""User ORM Model - aligns with diploma User class."""
from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class UserRole(str, PyEnum):
    """User roles from diploma."""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class UserORM(Base):
    """
    User entity from diploma diagram.
    
    Attributes:
        id: Primary key
        name: User name
        email: Unique email (for verification)
        password_hash: Hashed password
        role: User role (patient/doctor/admin)
        is_verified: Email verification status
        created_at: Registration timestamp
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PATIENT, nullable=False)
    
    # Email verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    
    # Doctor-specific fields (nullable for patients)
    specialization = Column(String(100), nullable=True)
    
    # Patient-specific fields (nullable for doctors)
    primary_doctor_id = Column(Integer, nullable=True)
    threshold_profile_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships to other models (lazy="dynamic" for pagination)
    measurements = relationship("MeasurementORM", back_populates="user", lazy="dynamic")
    medications = relationship("MedicationORM", back_populates="patient", lazy="dynamic")
    medication_intakes = relationship("MedicationIntakeORM", back_populates="patient", lazy="dynamic")
    activities = relationship("ActivityEventORM", back_populates="patient", lazy="dynamic")
    recommendations = relationship("RecommendationORM", back_populates="patient", lazy="dynamic")
    reports = relationship(
        "ReportORM", 
        foreign_keys="ReportORM.patient_id",
        back_populates="patient", 
        lazy="dynamic"
    )
    daily_summaries = relationship("DailySummaryORM", back_populates="patient", lazy="dynamic")
    audit_logs = relationship("AuditLogEntryORM", back_populates="user", lazy="dynamic")
    
    # One-to-one relationships
    threshold_profile = relationship("ThresholdProfileORM", back_populates="patient", uselist=False)
    
    def __repr__(self) -> str:
        return f"<UserORM(id={self.id}, email={self.email}, role={self.role.value})>"

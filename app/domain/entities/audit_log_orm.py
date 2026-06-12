"""AuditLog ORM Model - from diploma AuditService class."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class AuditLogEntryORM(Base):
    """
    AuditLogEntry entity - records all user actions for security.
    
    From diploma: AuditService.log(userId, action, details)
    
    Attributes:
        id: Primary key
        user_id: FK to users (who performed action)
        action: Action type (measurement_created, login, etc.)
        details: JSON string with action details
        ip_address: Optional IP address
        user_agent: Optional browser/client info
        timestamp: When action occurred
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    action = Column(String(100), nullable=False, index=True)  # measurement_created, login, logout, etc.
    entity_type = Column(String(50), nullable=True)  # measurement, user, report, etc.
    entity_id = Column(Integer, nullable=True)  # ID of affected entity
    details = Column(Text, nullable=True)  # JSON string with context
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(255), nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_audit_user_action', 'user_id', 'action'),
        Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_action_timestamp', 'action', 'timestamp'),
    )
    
    # Relationships
    user = relationship("UserORM", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLogEntryORM(id={self.id}, user_id={self.user_id}, action={self.action}, time={self.timestamp})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

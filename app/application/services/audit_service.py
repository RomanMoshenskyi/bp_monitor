"""AuditService - logging user actions from diploma class diagram."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.domain.entities import AuditLogEntryORM

_logger = logging.getLogger(__name__)


class AuditService:
    """
    Audit logging service.
    
    From diploma class diagram: AuditService.log(userId, action, details)
    """
    
    def __init__(self, db: Session):
        self._db = db
    
    def log(
        self,
        user_id: int,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntryORM:
        """
        Log a user action.
        
        Args:
            user_id: ID of user performing action
            action: Action type (measurement_created, login, etc.)
            entity_type: Type of affected entity (measurement, user, etc.)
            entity_id: ID of affected entity
            details: Additional context as dict
            ip_address: Client IP address
            user_agent: Client user agent string
        """
        entry = AuditLogEntryORM(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details, default=str) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
        )
        
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)
        
        _logger.debug(f"Audit: {action} by user {user_id}")
        
        return entry
    
    def get_user_actions(
        self,
        user_id: int,
        limit: int = 100,
        action_filter: Optional[str] = None,
    ) -> List[AuditLogEntryORM]:
        """Get audit log for a specific user."""
        from sqlalchemy import select, desc
        
        stmt = select(AuditLogEntryORM).where(
            AuditLogEntryORM.user_id == user_id
        )
        
        if action_filter:
            stmt = stmt.where(AuditLogEntryORM.action == action_filter)
        
        stmt = stmt.order_by(desc(AuditLogEntryORM.timestamp)).limit(limit)
        
        return list(self._db.execute(stmt).scalars().all())
    
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
    ) -> List[AuditLogEntryORM]:
        """Get audit history for a specific entity."""
        from sqlalchemy import select, desc
        
        stmt = (
            select(AuditLogEntryORM)
            .where(
                AuditLogEntryORM.entity_type == entity_type,
                AuditLogEntryORM.entity_id == entity_id,
            )
            .order_by(desc(AuditLogEntryORM.timestamp))
            .limit(limit)
        )
        
        return list(self._db.execute(stmt).scalars().all())
    
    def get_recent_actions(
        self,
        limit: int = 100,
        action_filter: Optional[str] = None,
    ) -> List[AuditLogEntryORM]:
        """Get recent actions across all users."""
        from sqlalchemy import select, desc
        
        stmt = select(AuditLogEntryORM)
        
        if action_filter:
            stmt = stmt.where(AuditLogEntryORM.action == action_filter)
        
        stmt = stmt.order_by(desc(AuditLogEntryORM.timestamp)).limit(limit)
        
        return list(self._db.execute(stmt).scalars().all())
    
    def get_summary_by_action(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, int]:
        """Get summary count of actions by type in date range."""
        from sqlalchemy import select, func
        
        stmt = (
            select(
                AuditLogEntryORM.action,
                func.count().label('count')
            )
            .where(
                AuditLogEntryORM.timestamp >= start_date,
                AuditLogEntryORM.timestamp <= end_date,
            )
            .group_by(AuditLogEntryORM.action)
        )
        
        results = self._db.execute(stmt).all()
        return {row.action: row.count for row in results}

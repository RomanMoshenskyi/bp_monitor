"""Recommendation Repository - ORM version."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session

from app.domain.entities import RecommendationORM, SeverityLevel


class RecommendationRepositoryORM:
    """Repository for RecommendationORM operations."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def get_by_id(self, recommendation_id: int) -> Optional[RecommendationORM]:
        """Get recommendation by ID."""
        return self._db.get(RecommendationORM, recommendation_id)
    
    def get_by_patient(
        self, 
        patient_id: int, 
        unread_only: bool = False,
        skip: int = 0, 
        limit: int = 50
    ) -> List[RecommendationORM]:
        """Get recommendations for a patient."""
        stmt = select(RecommendationORM).where(
            RecommendationORM.patient_id == patient_id
        )
        
        if unread_only:
            stmt = stmt.where(RecommendationORM.is_read == "N")
        
        stmt = stmt.order_by(
            desc(RecommendationORM.created_at)
        ).offset(skip).limit(limit)
        
        return list(self._db.execute(stmt).scalars().all())
    
    def get_critical_for_patient(self, patient_id: int) -> List[RecommendationORM]:
        """Get critical/high severity recommendations."""
        stmt = (
            select(RecommendationORM)
            .where(
                and_(
                    RecommendationORM.patient_id == patient_id,
                    RecommendationORM.severity.in_([SeverityLevel.HIGH, SeverityLevel.CRITICAL]),
                    RecommendationORM.is_read == "N"
                )
            )
            .order_by(desc(RecommendationORM.created_at))
        )
        return list(self._db.execute(stmt).scalars().all())
    
    def create(self, recommendation: RecommendationORM) -> RecommendationORM:
        """Create new recommendation."""
        self._db.add(recommendation)
        self._db.commit()
        self._db.refresh(recommendation)
        return recommendation
    
    def mark_as_read(self, recommendation_id: int) -> bool:
        """Mark recommendation as read."""
        rec = self.get_by_id(recommendation_id)
        if rec:
            rec.mark_as_read()
            self._db.commit()
            return True
        return False
    
    def acknowledge(self, recommendation_id: int) -> bool:
        """Patient acknowledges recommendation."""
        rec = self.get_by_id(recommendation_id)
        if rec:
            rec.acknowledge()
            self._db.commit()
            return True
        return False
    
    def delete(self, recommendation_id: int) -> bool:
        """Delete recommendation."""
        rec = self.get_by_id(recommendation_id)
        if rec:
            self._db.delete(rec)
            self._db.commit()
            return True
        return False

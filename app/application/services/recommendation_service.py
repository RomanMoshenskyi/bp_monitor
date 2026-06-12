"""RecommendationService - from diploma class diagram."""
from __future__ import annotations

import logging
from typing import List
from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.entities import RecommendationORM, MeasurementORM, SeverityLevel, UserORM
from app.application.dto import (
    RecommendationDTO, 
    RecommendationCreateDTO,
    AnalysisResultDTO,
)

_logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Recommendation generation service.
    
    From diploma class diagram: RecommendationService.generate()
    """
    
    def __init__(self, db: Session):
        self._db = db
    
    def generate(
        self,
        measurement: MeasurementORM,
        analysis: AnalysisResultDTO,
        patient: UserORM,
    ) -> List[RecommendationDTO]:
        """
        Generate personalized recommendations based on analysis.
        
        Args:
            measurement: Latest measurement
            analysis: Analysis result with stats and warnings
            patient: Patient user entity
        
        Returns:
            List of created recommendations
        """
        recommendations = []
        
        # Check for critical BP levels
        if measurement.systolic > 180 or measurement.diastolic > 110:
            rec = self._create_recommendation(
                patient_id=patient.id,
                measurement_id=measurement.id,
                severity=SeverityLevel.CRITICAL,
                category="medical",
                message="КРИТИЧНІЙ РІВЕНЬ ТИСКУ! Рекомендується негайно звернутися до лікаря.",
            )
            recommendations.append(rec)
        
        elif measurement.systolic > 140 or measurement.diastolic > 90:
            rec = self._create_recommendation(
                patient_id=patient.id,
                measurement_id=measurement.id,
                severity=SeverityLevel.HIGH,
                category="medical",
                message="Високий артеріальний тиск. Рекомендується консультація з лікарем та моніторинг.",
            )
            recommendations.append(rec)
        
        elif measurement.systolic < 90 or measurement.diastolic < 60:
            rec = self._create_recommendation(
                patient_id=patient.id,
                measurement_id=measurement.id,
                severity=SeverityLevel.MEDIUM,
                category="medical",
                message="Низький артеріальний тиск. Зверніть увагу на самопочуття.",
            )
            recommendations.append(rec)
        
        # Weather correlation recommendations
        if analysis.bp_weather_correlation and analysis.bp_weather_correlation.is_significant(0.5):
            rec = self._create_recommendation(
                patient_id=patient.id,
                measurement_id=measurement.id,
                severity=SeverityLevel.LOW,
                category="lifestyle",
                message=f"Виявлено зв'язок з погодою: {analysis.bp_weather_correlation.interpretation}. "
                        f"Рекомендується уважніше стежити за самопочуттям при змінах атмосферного тиску.",
            )
            recommendations.append(rec)
        
        _logger.info(f"Generated {len(recommendations)} recommendations for patient {patient.id}")
        
        return [self._to_dto(r) for r in recommendations]
    
    def _create_recommendation(
        self,
        patient_id: int,
        measurement_id: int,
        severity: SeverityLevel,
        category: str,
        message: str,
    ) -> RecommendationORM:
        """Create and save a recommendation."""
        rec = RecommendationORM(
            patient_id=patient_id,
            measurement_id=measurement_id,
            severity=severity,
            category=category,
            message=message,
            is_read="N",
            is_acknowledged="N",
        )
        
        self._db.add(rec)
        self._db.commit()
        self._db.refresh(rec)
        
        return rec
    
    def get_for_patient(
        self, 
        patient_id: int, 
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[RecommendationDTO]:
        """Get recommendations for a patient."""
        from sqlalchemy import select, desc
        
        stmt = select(RecommendationORM).where(
            RecommendationORM.patient_id == patient_id
        )
        
        if unread_only:
            stmt = stmt.where(RecommendationORM.is_read == "N")
        
        stmt = stmt.order_by(desc(RecommendationORM.created_at)).limit(limit)
        
        results = self._db.execute(stmt).scalars().all()
        return [self._to_dto(r) for r in results]
    
    def mark_as_read(self, recommendation_id: int) -> bool:
        """Mark recommendation as read."""
        rec = self._db.get(RecommendationORM, recommendation_id)
        if rec:
            rec.mark_as_read()
            self._db.commit()
            return True
        return False
    
    def acknowledge(self, recommendation_id: int) -> bool:
        """Patient acknowledges recommendation."""
        rec = self._db.get(RecommendationORM, recommendation_id)
        if rec:
            rec.acknowledge()
            self._db.commit()
            return True
        return False
    
    def _to_dto(self, rec: RecommendationORM) -> RecommendationDTO:
        """Convert ORM to DTO."""
        return RecommendationDTO(
            id=rec.id,
            patient_id=rec.patient_id,
            measurement_id=rec.measurement_id,
            severity=rec.severity,
            category=rec.category,
            message=rec.message,
            is_read=rec.is_read == "Y",
            is_acknowledged=rec.is_acknowledged == "Y",
            created_at=rec.created_at,
        )

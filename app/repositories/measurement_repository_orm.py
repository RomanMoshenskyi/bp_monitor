"""Measurement Repository - ORM version."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.domain.entities import MeasurementORM


class MeasurementRepositoryORM:
    """Repository for MeasurementORM operations."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def get_by_id(self, measurement_id: int) -> Optional[MeasurementORM]:
        """Get measurement by ID."""
        return self._db.get(MeasurementORM, measurement_id)
    
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[MeasurementORM]:
        """Get measurements for a user with pagination."""
        stmt = (
            select(MeasurementORM)
            .where(MeasurementORM.user_id == user_id)
            .order_by(MeasurementORM.measured_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.execute(stmt).scalars().all())
    
    def get_by_user_and_date_range(
        self, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MeasurementORM]:
        """Get measurements within date range."""
        stmt = (
            select(MeasurementORM)
            .where(
                and_(
                    MeasurementORM.user_id == user_id,
                    MeasurementORM.measured_at >= start_date,
                    MeasurementORM.measured_at <= end_date
                )
            )
            .order_by(MeasurementORM.measured_at)
        )
        return list(self._db.execute(stmt).scalars().all())
    
    def get_latest_for_user(self, user_id: int) -> Optional[MeasurementORM]:
        """Get latest measurement for user."""
        stmt = (
            select(MeasurementORM)
            .where(MeasurementORM.user_id == user_id)
            .order_by(MeasurementORM.measured_at.desc())
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none()
    
    def create(self, measurement: MeasurementORM) -> MeasurementORM:
        """Create new measurement."""
        self._db.add(measurement)
        self._db.commit()
        self._db.refresh(measurement)
        return measurement
    
    def update(self, measurement: MeasurementORM) -> MeasurementORM:
        """Update measurement."""
        self._db.merge(measurement)
        self._db.commit()
        self._db.refresh(measurement)
        return measurement
    
    def delete(self, measurement_id: int) -> bool:
        """Delete measurement."""
        measurement = self.get_by_id(measurement_id)
        if measurement:
            self._db.delete(measurement)
            self._db.commit()
            return True
        return False
    
    def count_by_user(self, user_id: int) -> int:
        """Count measurements for user."""
        stmt = select(func.count()).where(MeasurementORM.user_id == user_id)
        return self._db.execute(stmt).scalar()
    
    def get_with_weather(self, user_id: int, limit: int = 100) -> List[MeasurementORM]:
        """Get measurements with weather data."""
        stmt = (
            select(MeasurementORM)
            .where(
                and_(
                    MeasurementORM.user_id == user_id,
                    MeasurementORM.weather_snapshot_id.isnot(None)
                )
            )
            .order_by(MeasurementORM.measured_at.desc())
            .limit(limit)
        )
        return list(self._db.execute(stmt).scalars().all())

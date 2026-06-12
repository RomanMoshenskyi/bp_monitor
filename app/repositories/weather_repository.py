"""Weather Snapshot Repository - ORM version."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.domain.entities import WeatherSnapshotORM


class WeatherRepository:
    """Repository for WeatherSnapshotORM operations."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def get_by_id(self, snapshot_id: int) -> Optional[WeatherSnapshotORM]:
        """Get weather snapshot by ID."""
        return self._db.get(WeatherSnapshotORM, snapshot_id)
    
    def get_by_city_and_time(
        self, 
        city: str, 
        recorded_at: datetime, 
        window_minutes: int = 30
    ) -> Optional[WeatherSnapshotORM]:
        """
        Get weather snapshot for city around specific time.
        Used to find existing snapshot before creating new one.
        """
        time_window = timedelta(minutes=window_minutes)
        stmt = (
            select(WeatherSnapshotORM)
            .where(
                and_(
                    WeatherSnapshotORM.city == city,
                    WeatherSnapshotORM.recorded_at >= recorded_at - time_window,
                    WeatherSnapshotORM.recorded_at <= recorded_at + time_window
                )
            )
            .order_by(func.abs(WeatherSnapshotORM.recorded_at - recorded_at))
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none()
    
    def get_latest_for_city(self, city: str) -> Optional[WeatherSnapshotORM]:
        """Get latest weather snapshot for a city."""
        stmt = (
            select(WeatherSnapshotORM)
            .where(WeatherSnapshotORM.city == city)
            .order_by(WeatherSnapshotORM.recorded_at.desc())
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none()
    
    def create(self, snapshot: WeatherSnapshotORM) -> WeatherSnapshotORM:
        """Create new weather snapshot."""
        self._db.add(snapshot)
        self._db.commit()
        self._db.refresh(snapshot)
        return snapshot
    
    def delete_old_snapshots(self, city: str, older_than_days: int = 30) -> int:
        """Delete weather snapshots older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        stmt = select(WeatherSnapshotORM).where(
            and_(
                WeatherSnapshotORM.city == city,
                WeatherSnapshotORM.recorded_at < cutoff_date
            )
        )
        old_snapshots = self._db.execute(stmt).scalars().all()
        count = len(old_snapshots)
        for snapshot in old_snapshots:
            self._db.delete(snapshot)
        self._db.commit()
        return count

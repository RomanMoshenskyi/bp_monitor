"""Base Repository pattern - abstract base for all repositories."""
from __future__ import annotations

from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic base repository implementing common CRUD operations.
    
    All domain repositories inherit from this class.
    """
    
    def __init__(self, db: Session, model_class: Type[T]):
        self._db = db
        self._model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by primary key."""
        return self._db.get(self._model_class, id)
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        stmt = select(self._model_class).offset(skip).limit(limit)
        return list(self._db.execute(stmt).scalars().all())
    
    def create(self, entity: T) -> T:
        """Create new entity."""
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity
    
    def update(self, entity: T) -> T:
        """Update existing entity."""
        self._db.merge(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity
    
    def delete(self, id: int) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        entity = self.get_by_id(id)
        if entity:
            self._db.delete(entity)
            self._db.commit()
            return True
        return False
    
    def count(self) -> int:
        """Count all entities."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self._model_class)
        return self._db.execute(stmt).scalar()

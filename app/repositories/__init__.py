# Legacy repositories (psycopg2-based)
from .assignment_repository import AssignmentRepository
from .measurement_repository import MeasurementRepository
from .recommendation_repository import RecommendationRepository
from .user_repository import UserRepository

# New ORM repositories
from .base_repository import BaseRepository
from .user_repository_orm import UserRepositoryORM
from .measurement_repository_orm import MeasurementRepositoryORM
from .weather_repository import WeatherRepository
from .recommendation_repository_orm import RecommendationRepositoryORM

__all__ = [
    # Legacy
    "AssignmentRepository",
    "MeasurementRepository",
    "RecommendationRepository",
    "UserRepository",
    # ORM
    "BaseRepository",
    "UserRepositoryORM",
    "MeasurementRepositoryORM",
    "WeatherRepository",
    "RecommendationRepositoryORM",
]

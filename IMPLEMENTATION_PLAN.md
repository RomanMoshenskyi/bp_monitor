# План реалізації: Система моніторингу кров'яного тиску (Desktop Application)

## Вступ

Цей документ описує покроковий план перетворення поточного прототипу на production-ready desktop застосунок для моніторингу кров'яного тиску з урахуванням атмосферного тиску.

**Поточний стан:** Working prototype (3.8/10 production readiness)
**Цільовий стан:** Production-ready desktop application (8.5+/10)

---

## Phase 1: Критичні виправлення (Priority: P0)

### Step 1.1: Виправити connection pooling

**Проблема:** Кожен `db_cursor()` створює нове з'єднання з PostgreSQL.

**Рішення:** Додати connection pooling через `psycopg2.pool`.

**Файл:** `app/database.py`

**Дії:**
1. Додати імпорт:
```python
from psycopg2 import pool
from threading import Lock
```

2. Додати глобальний connection pool:
```python
_connection_pool: pool.ThreadedConnectionPool | None = None
_pool_lock = Lock()

def get_connection_pool() -> pool.ThreadedConnectionPool:
    global _connection_pool
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=DB_CONFIG["host"],
                    port=DB_CONFIG["port"],
                    dbname=DB_CONFIG["database"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    connect_timeout=5,
                    options="-c client_encoding=UTF8",
                )
    return _connection_pool
```

3. Оновити `db_cursor()`:
```python
@contextmanager
def db_cursor() -> Generator[PgCursor, None, None]:
    pool = get_connection_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
```

4. Додати функцію закриття pool:
```python
def close_connection_pool() -> None:
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
```

**Перевірка:** Запустити застосунок, переконатися що з'єднання працюють.

---

### Step 1.2: Усилити password policy

**Проблема:** Мінімум 4 символи - критично слабко.

**Рішення:** Змінити на 8 символів + complexity requirements.

**Файл:** `app/auth.py`

**Дії:**
1. Замінити валідацію пароля (line 129-130):
```python
def _validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Пароль має містити щонайменше 8 символів")
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        raise ValueError(
            "Пароль має містити хоча б одну велику літеру, "
            "одну малу літеру та одну цифру"
        )
```

2. Оновити `_insert_user()`:
```python
def _insert_user(self, username: str, password: str, full_name: str, role: str, 
                 age: Optional[int] = None, email: Optional[str] = None) -> User:
    _validate_password_strength(password)  # Додати цей рядок
    uname = username.strip().lower()
    # ... решта коду
```

3. Оновити демо-паролі в `app/migrations.py` та `scripts/seed_patients.py`:
```python
# Замінити слабкі паролі на сильні
("admin", "AdminPass123", "Адміністратор", ROLE_ADMIN),
("doctor", "DoctorPass123", "Лікар Іваненко", ROLE_DOCTOR),
("patient", "PatientPass123", "Пацієнт Демо", ROLE_PATIENT),
```

4. Оновити UI підказку в `app/login_window.py` (line 77):
```python
hint = QLabel("Демо: admin/AdminPass123 · doctor/DoctorPass123 · patient/PatientPass123")
```

**Перевірка:** Спробувати зареєструвати користувача зі слабким паролем - має бути помилка.

---

### Step 1.3: Виправити cascade delete

**Проблема:** `ON DELETE CASCADE` видаляє всі measurements при видаленні користувача.

**Рішення:** Змінити на `ON DELETE SET NULL` або додати soft delete.

**Файл:** `schema_auth.sql`

**Дії:**
1. Замінити line 40-41:
```sql
-- Замінити:
-- patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
-- На:
patient_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
```

2. Додати soft delete mechanism (створити нову міграцію):

**Файл:** `migrations/004_add_soft_delete.sql`
```sql
-- Додати soft delete колонку
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Додати soft delete колонку для users
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Створити індекс для швидкого пошуку не видалених записів
CREATE INDEX IF NOT EXISTS idx_measurements_not_deleted ON measurements(user_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_not_deleted ON users WHERE deleted_at IS NULL;
```

3. Оновити `app/storage.py` - додати soft delete методи:
```python
def soft_delete_measurement(self, measurement_id: str, patient_id: Optional[int] = None) -> None:
    pid = patient_id or self.user.id
    with db_cursor() as cur:
        cur.execute(
            "UPDATE measurements SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s",
            (measurement_id, pid),
        )

def soft_delete_user(self, user_id: int) -> None:
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s",
            (user_id,),
        )
```

4. Оновити `app/main_window.py` - використовувати soft delete:
```python
# У MeasurementsPage._delete_selected():
self.delete_callback(measurement.id)  # Замінити на soft delete
```

**Перевірка:** Видалити користувача - measurements мають залишитися з `deleted_at` timestamp.

---

### Step 1.4: Додати server-side validation

**Проблема:** Валідація тільки на UI, немає server-side validation layer.

**Рішення:** Створити ValidationService.

**Файл:** `app/services/validation_service.py` (новий)

**Дії:**
1. Створити файл:
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidationError:
    field: str
    message: str


class ValidationService:
    def validate_measurement(
        self,
        systolic: int,
        diastolic: int,
        pulse: int,
        timestamp: str,
    ) -> List[ValidationError]:
        errors: List[ValidationError] = []
        
        # Валідація тиску
        if systolic <= diastolic:
            errors.append(ValidationError(
                "systolic",
                "Систолічний тиск має бути більшим за діастолічний"
            ))
        
        if not (60 <= systolic <= 240):
            errors.append(ValidationError(
                "systolic",
                "Систолічний тиск має бути в діапазоні 60-240 мм рт. ст."
            ))
        
        if not (40 <= diastolic <= 150):
            errors.append(ValidationError(
                "diastolic",
                "Діастолічний тиск має бути в діапазоні 40-150 мм рт. ст."
            ))
        
        if not (35 <= pulse <= 220):
            errors.append(ValidationError(
                "pulse",
                "Пульс має бути в діапазоні 35-220 уд/хв"
            ))
        
        # Валідація timestamp
        from datetime import datetime
        try:
            datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        except ValueError:
            errors.append(ValidationError(
                "timestamp",
                "Некоректний формат дати та часу. Очікується: YYYY-MM-DD HH:MM"
            ))
        
        return errors
    
    def validate_user_profile(
        self,
        name: str,
        age: int,
        target_systolic: int,
        target_diastolic: int,
        target_pulse: int,
    ) -> List[ValidationError]:
        errors: List[ValidationError] = []
        
        if not name or len(name.strip()) < 2:
            errors.append(ValidationError(
                "name",
                "Ім'я має містити щонайменше 2 символи"
            ))
        
        if not (1 <= age <= 120):
            errors.append(ValidationError(
                "age",
                "Вік має бути в діапазоні 1-120 років"
            ))
        
        if not (80 <= target_systolic <= 180):
            errors.append(ValidationError(
                "target_systolic",
                "Цільовий систолічний тиск має бути в діапазоні 80-180"
            ))
        
        if not (50 <= target_diastolic <= 120):
            errors.append(ValidationError(
                "target_diastolic",
                "Цільовий діастолічний тиск має бути в діапазоні 50-120"
            ))
        
        if not (40 <= target_pulse <= 150):
            errors.append(ValidationError(
                "target_pulse",
                "Цільовий пульс має бути в діапазоні 40-150"
            ))
        
        if target_systolic <= target_diastolic:
            errors.append(ValidationError(
                "target_systolic",
                "Цільовий систолічний тиск має бути більшим за цільовий діастолічний"
            ))
        
        return errors
```

2. Оновити `app/storage.py` - додати валідацію в `add_measurement()`:
```python
from .services.validation_service import ValidationService

class PostgresStorage:
    def __init__(self, user: User) -> None:
        init_schema()
        self.user = user
        self._validation_service = ValidationService()
    
    def add_measurement(self, measurement: Measurement, patient_id: Optional[int] = None) -> None:
        # Валідація
        errors = self._validation_service.validate_measurement(
            measurement.systolic,
            measurement.diastolic,
            measurement.pulse,
            measurement.timestamp,
        )
        if errors:
            error_messages = ", ".join(f"{e.field}: {e.message}" for e in errors)
            raise ValueError(f"Валідація не пройшла: {error_messages}")
        
        # ... решта коду
```

3. Оновити `app/main_window.py` - обробляти validation errors:
```python
def _add_measurement(self):
    try:
        # ... створення measurement
        self.add_callback(measurement)
        self._clear_form()
        QMessageBox.information(self, "Успіх", "Вимірювання збережено")
    except ValueError as e:
        QMessageBox.warning(self, "Помилка валідації", str(e))
```

**Перевірка:** Спробувати створити вимірювання з некоректними даними - має бути помилка валідації.

---

### Step 1.5: Додати базові unit тести

**Проблема:** Нульове покриття тестами.

**Рішення:** Створити базові unit тести для критичних компонентів.

**Файл:** `tests/__init__.py` (новий)
```python
# Empty file for package
```

**Файл:** `tests/test_analytics.py` (новий)
```python
import pytest
from datetime import datetime, timedelta
from app.analytics import (
    correlation_atmospheric,
    filter_by_days,
    generate_recommendations,
    pressure_status,
    summary,
)
from app.storage import Measurement


def test_pressure_status():
    assert pressure_status(115, 75) == "Норма"
    assert pressure_status(125, 78) == "Підвищений"
    assert pressure_status(135, 85) == "Гіпертензія I"
    assert pressure_status(145, 95) == "Гіпертензія II"
    assert pressure_status(85, 55) == "Знижений"


def test_filter_by_days():
    now = datetime.now()
    measurements = [
        Measurement(
            id="1",
            timestamp=(now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            systolic=120,
            diastolic=80,
            pulse=72,
        ),
        Measurement(
            id="2",
            timestamp=(now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
            systolic=125,
            diastolic=82,
            pulse=75,
        ),
    ]
    
    recent = filter_by_days(measurements, 7)
    assert len(recent) == 1
    assert recent[0].id == "1"


def test_correlation_atmospheric():
    measurements = [
        Measurement(id="1", timestamp="2024-01-01 10:00", systolic=120, diastolic=80, pulse=72, atmospheric_pressure=745),
        Measurement(id="2", timestamp="2024-01-02 10:00", systolic=125, diastolic=82, pulse=75, atmospheric_pressure=750),
        Measurement(id="3", timestamp="2024-01-03 10:00", systolic=130, diastolic=85, pulse=78, atmospheric_pressure=755),
    ]
    
    corr = correlation_atmospheric(measurements)
    assert corr is not None
    assert -1 <= corr <= 1


def test_correlation_insufficient_data():
    measurements = [
        Measurement(id="1", timestamp="2024-01-01 10:00", systolic=120, diastolic=80, pulse=72, atmospheric_pressure=745),
    ]
    
    corr = correlation_atmospheric(measurements)
    assert corr is None


def test_summary_empty():
    stats = summary([])
    assert stats["count"] == 0
    assert stats["avg_systolic"] == 0
    assert stats["correlation"] is None


def test_generate_recommendations():
    measurements = [
        Measurement(id="1", timestamp="2024-01-01 10:00", systolic=145, diastolic=95, pulse=85, atmospheric_pressure=745),
    ]
    
    recs = generate_recommendations(measurements)
    assert len(recs) > 0
    assert any("підвищені значення" in r.lower() for r in recs)
```

**Файл:** `tests/test_validation.py` (новий)
```python
import pytest
from app.services.validation_service import ValidationService, ValidationError


def test_validate_measurement_valid():
    service = ValidationService()
    errors = service.validate_measurement(120, 80, 72, "2024-01-01 10:00")
    assert len(errors) == 0


def test_validate_measurement_systolic_too_low():
    service = ValidationService()
    errors = service.validate_measurement(50, 80, 72, "2024-01-01 10:00")
    assert len(errors) > 0
    assert any(e.field == "systolic" for e in errors)


def test_validate_measurement_systolic_less_than_diastolic():
    service = ValidationService()
    errors = service.validate_measurement(80, 120, 72, "2024-01-01 10:00")
    assert len(errors) > 0
    assert any("систолічний тиск має бути більшим" in e.message.lower() for e in errors)


def test_validate_measurement_invalid_timestamp():
    service = ValidationService()
    errors = service.validate_measurement(120, 80, 72, "invalid-date")
    assert len(errors) > 0
    assert any(e.field == "timestamp" for e in errors)


def test_validate_user_profile_valid():
    service = ValidationService()
    errors = service.validate_user_profile("Іван Петренко", 30, 120, 80, 72)
    assert len(errors) == 0


def test_validate_user_profile_name_too_short():
    service = ValidationService()
    errors = service.validate_user_profile("І", 30, 120, 80, 72)
    assert len(errors) > 0
    assert any(e.field == "name" for e in errors)


def test_validate_user_profile_age_invalid():
    service = ValidationService()
    errors = service.validate_user_profile("Іван Петренко", 150, 120, 80, 72)
    assert len(errors) > 0
    assert any(e.field == "age" for e in errors)
```

**Файл:** `requirements.txt` - додати pytest:
```txt
PyQt6>=6.7
psycopg2-binary>=2.9
pytest>=7.4
pytest-qt>=4.2
```

**Перевірка:** Запустити тести:
```bash
pytest tests/ -v
```

---

## Phase 2: Архітектурна стабілізація (Priority: P1)

### Step 2.1: Створити Service layer

**Проблема:** Бізнес-логіка розмазана по UI та storage.

**Рішення:** Створити окремий service layer.

**Файл:** `app/services/__init__.py` (новий)
```python
from .validation_service import ValidationService, ValidationError
from .measurement_service import MeasurementService
from .analytics_service import AnalyticsService
from .export_service import ExportService

__all__ = [
    "ValidationService",
    "ValidationError",
    "MeasurementService",
    "AnalyticsService",
    "ExportService",
]
```

**Файл:** `app/services/measurement_service.py` (новий)
```python
from __future__ import annotations

from typing import List, Optional

from app.analytics import summary
from app.storage import Measurement, PostgresStorage
from app.weather import fetch_atmospheric_pressure_mmhg
from .validation_service import ValidationService


class MeasurementService:
    def __init__(self, storage: PostgresStorage):
        self._storage = storage
        self._validation_service = ValidationService()
    
    def create_measurement(
        self,
        timestamp: str,
        systolic: int,
        diastolic: int,
        pulse: int,
        mood: str,
        notes: str,
        atmospheric_pressure: Optional[int],
        medication_taken: bool,
        activity_level: str,
        city: Optional[str] = None,
        patient_id: Optional[int] = None,
    ) -> Measurement:
        # Валідація
        errors = self._validation_service.validate_measurement(
            systolic, diastolic, pulse, timestamp
        )
        if errors:
            error_messages = ", ".join(f"{e.field}: {e.message}" for e in errors)
            raise ValueError(f"Валідація не пройшла: {error_messages}")
        
        # Отримати атмосферний тиск якщо не вказано але вказано місто
        if atmospheric_pressure is None and city:
            atmospheric_pressure = fetch_atmospheric_pressure_mmhg(city)
        
        # Створити measurement
        import uuid
        measurement = Measurement(
            id=uuid.uuid4().hex[:8],
            timestamp=timestamp,
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
            mood=mood,
            notes=notes,
            atmospheric_pressure=atmospheric_pressure,
            medication_taken=medication_taken,
            activity_level=activity_level,
        )
        
        # Зберегти
        self._storage.add_measurement(measurement, patient_id)
        
        return measurement
    
    def get_measurements(self, patient_id: Optional[int] = None) -> List[Measurement]:
        return self._storage.get_measurements(patient_id)
    
    def delete_measurement(self, measurement_id: str, patient_id: Optional[int] = None) -> None:
        self._storage.soft_delete_measurement(measurement_id, patient_id)
    
    def get_summary(self, patient_id: Optional[int] = None) -> dict:
        measurements = self.get_measurements(patient_id)
        return summary(measurements)
```

**Файл:** `app/services/analytics_service.py` (новий)
```python
from __future__ import annotations

from typing import List, Optional

from app.analytics import (
    correlation_atmospheric,
    filter_by_days,
    generate_recommendations,
    latest_measurement,
    pressure_status,
    summary,
)
from app.storage import Measurement


class AnalyticsService:
    def get_summary(self, measurements: List[Measurement]) -> dict:
        return summary(measurements)
    
    def get_correlation(self, measurements: List[Measurement]) -> Optional[float]:
        return correlation_atmospheric(measurements)
    
    def get_recommendations(self, measurements: List[Measurement]) -> List[str]:
        return generate_recommendations(measurements)
    
    def filter_by_period(self, measurements: List[Measurement], days: Optional[int]) -> List[Measurement]:
        if days is None:
            return measurements
        return filter_by_days(measurements, days)
    
    def get_latest(self, measurements: List[Measurement]) -> Optional[Measurement]:
        return latest_measurement(measurements)
    
    def get_pressure_status(self, systolic: int, diastolic: int) -> str:
        return pressure_status(systolic, diastolic)
```

**Файл:** `app/services/export_service.py` (новий)
```python
from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.storage import PostgresStorage


class ExportService:
    def __init__(self, storage: PostgresStorage):
        self._storage = storage
    
    def export_to_json(
        self,
        target_path: str | Path,
        patient_id: Optional[int] = None,
    ) -> None:
        self._storage.export_to_json(target_path, patient_id)
    
    def export_to_csv(
        self,
        target_path: str | Path,
        patient_id: Optional[int] = None,
    ) -> None:
        import csv
        from datetime import datetime
        
        measurements = self._storage.get_measurements(patient_id)
        target = Path(target_path)
        
        with target.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Timestamp", "Systolic", "Diastolic", "Pulse",
                "Mood", "Notes", "Atmospheric Pressure", "Medication Taken", "Activity Level"
            ])
            
            for m in measurements:
                writer.writerow([
                    m.id,
                    m.timestamp,
                    m.systolic,
                    m.diastolic,
                    m.pulse,
                    m.mood,
                    m.notes,
                    m.atmospheric_pressure or "",
                    "Yes" if m.medication_taken else "No",
                    m.activity_level,
                ])
```

**Перевірка:** Оновити `app/main_window.py` використовувати MeasurementService замість прямого виклику storage.

---

### Step 2.2: Розділити main_window.py

**Проблема:** 992 lines в одному файлі (God object).

**Рішення:** Розбити на окремі файли для кожної сторінки.

**Файл:** `app/ui/__init__.py` (новий)
```python
from .main_window import MainWindow
from .dashboard_page import DashboardPage
from .measurements_page import MeasurementsPage
from .analytics_page import AnalyticsPage
from .settings_page import SettingsPage

__all__ = [
    "MainWindow",
    "DashboardPage",
    "MeasurementsPage",
    "AnalyticsPage",
    "SettingsPage",
]
```

**Файл:** `app/ui/dashboard_page.py` (новий)
```python
# Скопіювати клас DashboardPage з main_window.py (lines 216-333)
# Змінити імпорти:
from app.widgets import GlassCard, PressureGauge, SectionTitle, TrendChart
from app.analytics import summary, latest_measurement, pressure_status
from app.storage import Measurement

class DashboardPage(QWidget):
    # ... код з main_window.py ...
```

**Файл:** `app/ui/measurements_page.py` (новий)
```python
# Скопіювати клас MeasurementsPage з main_window.py (lines 335-546)
from app.widgets import SectionTitle
from app.storage import Measurement
from app.weather import city_names, detect_city_by_ip, fetch_atmospheric_pressure_mmhg

class MeasurementsPage(QWidget):
    # ... код з main_window.py ...
```

**Файл:** `app/ui/analytics_page.py` (новий)
```python
# Скопіювати клас AnalyticsPage з main_window.py (lines 548-667)
from app.widgets import SectionTitle, TrendChart
from app.analytics import filter_by_days, generate_recommendations, summary
from app.storage import Measurement

class AnalyticsPage(QWidget):
    # ... код з main_window.py ...
```

**Файл:** `app/ui/settings_page.py` (новий)
```python
# Скопіювати клас SettingsPage з main_window.py (lines 669-751)
from app.widgets import SectionTitle

class SettingsPage(QWidget):
    # ... код з main_window.py ...
```

**Файл:** `app/ui/main_window.py` (новий)
```python
# Залишити тільки клас MainWindow та APP_STYLE
# Імпортувати сторінки:
from .dashboard_page import DashboardPage
from .measurements_page import MeasurementsPage
from .analytics_page import AnalyticsPage
from .settings_page import SettingsPage

class MainWindow(QMainWindow):
    # ... код з main_window.py (lines 753-992) ...
```

**Видалити:** `app/main_window.py` (після створення нових файлів)

**Перевірка:** Запустити застосунок, переконатися що всі сторінки працюють.

---

### Step 2.3: Створити Repository pattern

**Проблема:** PostgresStorage змішує repository responsibilities з business logic.

**Рішення:** Розділити на окремі repositories.

**Файл:** `app/repositories/__init__.py` (новий)
```python
from .measurement_repository import MeasurementRepository
from .user_repository import UserRepository
from .recommendation_repository import RecommendationRepository

__all__ = [
    "MeasurementRepository",
    "UserRepository",
    "RecommendationRepository",
]
```

**Файл:** `app/repositories/measurement_repository.py` (новий)
```python
from __future__ import annotations

from typing import List, Optional

from app.database import db_cursor
from app.storage import Measurement, _row_to_measurement, _parse_timestamp


class MeasurementRepository:
    def find_by_user_id(self, user_id: int) -> List[Measurement]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, timestamp, systolic, diastolic, pulse, mood, notes,
                       atmospheric_pressure, medication_taken, activity_level
                FROM measurements
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY timestamp
                """,
                (user_id,),
            )
            rows = cur.fetchall()
        return [_row_to_measurement(row) for row in rows]
    
    def save(self, measurement: Measurement, user_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO measurements (
                    id, user_id, timestamp, systolic, diastolic, pulse, mood, notes,
                    atmospheric_pressure, medication_taken, activity_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    systolic = EXCLUDED.systolic,
                    diastolic = EXCLUDED.diastolic,
                    pulse = EXCLUDED.pulse,
                    mood = EXCLUDED.mood,
                    notes = EXCLUDED.notes,
                    atmospheric_pressure = EXCLUDED.atmospheric_pressure,
                    medication_taken = EXCLUDED.medication_taken,
                    activity_level = EXCLUDED.activity_level
                """,
                (
                    measurement.id,
                    user_id,
                    _parse_timestamp(measurement.timestamp),
                    measurement.systolic,
                    measurement.diastolic,
                    measurement.pulse,
                    measurement.mood,
                    measurement.notes,
                    measurement.atmospheric_pressure,
                    measurement.medication_taken,
                    measurement.activity_level,
                ),
            )
    
    def soft_delete(self, measurement_id: str, user_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE measurements SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s",
                (measurement_id, user_id),
            )
    
    def delete(self, measurement_id: str, user_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "DELETE FROM measurements WHERE id = %s AND user_id = %s",
                (measurement_id, user_id),
            )
```

**Файл:** `app/repositories/user_repository.py` (новий)
```python
from __future__ import annotations

from typing import List, Optional

from app.auth import User, _row_to_user
from app.database import db_cursor


class UserRepository:
    def find_by_id(self, user_id: int) -> Optional[User]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, full_name, role, age,
                       target_systolic, target_diastolic, target_pulse, is_active, email
                FROM users
                WHERE id = %s AND deleted_at IS NULL
                """,
                (user_id,),
            )
            row = cur.fetchone()
        return _row_to_user(row) if row else None
    
    def find_by_username(self, username: str) -> Optional[User]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, full_name, role, age,
                       target_systolic, target_diastolic, target_pulse, is_active, email
                FROM users
                WHERE username = %s AND deleted_at IS NULL
                """,
                (username.lower(),),
            )
            row = cur.fetchone()
        return _row_to_user(row) if row else None
    
    def find_by_role(self, role: str) -> List[User]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, full_name, role, age,
                       target_systolic, target_diastolic, target_pulse, is_active, email
                FROM users
                WHERE role = %s AND deleted_at IS NULL
                ORDER BY full_name
                """,
                (role,),
            )
            rows = cur.fetchall()
        return [_row_to_user(r) for r in rows]
    
    def save(self, user: User) -> User:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    username, password_hash, full_name, role, age, email,
                    target_systolic, target_diastolic, target_pulse
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    age = EXCLUDED.age,
                    email = EXCLUDED.email,
                    target_systolic = EXCLUDED.target_systolic,
                    target_diastolic = EXCLUDED.target_diastolic,
                    target_pulse = EXCLUDED.target_pulse
                RETURNING id, username, password_hash, full_name, role, age,
                          target_systolic, target_diastolic, target_pulse, is_active, email
                """,
                (
                    user.username,
                    user.password_hash if hasattr(user, 'password_hash') else '',
                    user.full_name,
                    user.role,
                    user.age,
                    user.email,
                    user.target_systolic,
                    user.target_diastolic,
                    user.target_pulse,
                ),
            )
            row = cur.fetchone()
        return _row_to_user(row)
    
    def update_thresholds(
        self,
        user_id: int,
        target_systolic: int,
        target_diastolic: int,
        target_pulse: int,
        age: Optional[int] = None,
    ) -> None:
        with db_cursor() as cur:
            if age is not None:
                cur.execute(
                    """
                    UPDATE users
                    SET target_systolic = %s, target_diastolic = %s, target_pulse = %s, age = %s
                    WHERE id = %s
                    """,
                    (target_systolic, target_diastolic, target_pulse, age, user_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE users
                    SET target_systolic = %s, target_diastolic = %s, target_pulse = %s
                    WHERE id = %s
                    """,
                    (target_systolic, target_diastolic, target_pulse, user_id),
                )
    
    def soft_delete(self, user_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s",
                (user_id,),
            )
```

**Файл:** `app/repositories/recommendation_repository.py` (новий)
```python
from __future__ import annotations

from typing import List

from app.database import db_cursor


class RecommendationRepository:
    def add(self, patient_id: int, doctor_id: int, text: str) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO doctor_recommendations (patient_id, doctor_id, recommendation)
                VALUES (%s, %s, %s)
                """,
                (patient_id, doctor_id, text.strip()),
            )
    
    def find_by_patient_id(self, patient_id: int, limit: int = 20) -> List[str]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT recommendation FROM doctor_recommendations
                WHERE patient_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (patient_id, limit),
            )
            rows = cur.fetchall()
        return [r[0] for r in rows]
```

**Перевірка:** Оновити `app/storage.py` використовувати repositories замість прямих SQL запитів.

---

### Step 2.4: Оновити Storage використовувати Repositories

**Файл:** `app/storage.py`

**Дії:**
1. Додати імпорти:
```python
from .repositories import (
    MeasurementRepository,
    UserRepository,
    RecommendationRepository,
)
```

2. Оновити PostgresStorage:
```python
class PostgresStorage:
    def __init__(self, user: User) -> None:
        init_schema()
        self.user = user
        self._measurement_repo = MeasurementRepository()
        self._user_repo = UserRepository()
        self._recommendation_repo = RecommendationRepository()
    
    def get_measurements(self, patient_id: Optional[int] = None) -> List[Measurement]:
        pid = patient_id or self.user.id
        return self._measurement_repo.find_by_user_id(pid)
    
    def add_measurement(self, measurement: Measurement, patient_id: Optional[int] = None) -> None:
        pid = patient_id or self.user.id
        self._measurement_repo.save(measurement, pid)
    
    def delete_measurement(self, measurement_id: str, patient_id: Optional[int] = None) -> None:
        pid = patient_id or self.user.id
        self._measurement_repo.soft_delete(measurement_id, pid)
    
    def get_profile(self) -> Dict[str, Any]:
        u = self._user_repo.find_by_id(self.user.id)
        return {
            "name": u.full_name,
            "age": u.age or 28,
            "target_systolic": u.target_systolic,
            "target_diastolic": u.target_diastolic,
            "target_pulse": u.target_pulse,
        }
    
    def update_profile(self, profile: Dict[str, Any]) -> None:
        self._user_repo.update_thresholds(
            self.user.id,
            profile.get("target_systolic", 120),
            profile.get("target_diastolic", 80),
            profile.get("target_pulse", 75),
            profile.get("age"),
        )
        # Оновити локальний user object
        self.user.full_name = profile.get("name", self.user.full_name)
        self.user.age = profile.get("age", self.user.age)
        self.user.target_systolic = profile.get("target_systolic", self.user.target_systolic)
        self.user.target_diastolic = profile.get("target_diastolic", self.user.target_diastolic)
        self.user.target_pulse = profile.get("target_pulse", self.user.target_pulse)
    
    def add_doctor_recommendation(self, patient_id: int, text: str) -> None:
        self._recommendation_repo.add(patient_id, self.user.id, text)
    
    def get_doctor_recommendations(self, patient_id: int, limit: int = 20) -> List[str]:
        return self._recommendation_repo.find_by_patient_id(patient_id, limit)
```

**Перевірка:** Запустити застосунок, переконатися що всі операції працюють.

---

## Phase 3: Покращення функціональності (Priority: P2)

### Step 3.1: Додати caching для Weather API

**Проблема:** Немає кешування, кожен запит до API.

**Рішення:** Додати in-memory caching з TTL.

**Файл:** `app/weather.py`

**Дії:**
1. Додати caching:
```python
from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.request
from typing import Optional, Tuple
from functools import lru_cache
from datetime import timedelta, datetime

# ... існуючий код CITIES, _haversine_km, nearest_city ...

# Cache storage
_weather_cache: dict[str, tuple[int, datetime]] = {}
_CACHE_TTL = timedelta(minutes=30)  # Кешувати на 30 хвилин


def _get_cached_pressure(city: str) -> Optional[int]:
    if city in _weather_cache:
        pressure, cached_at = _weather_cache[city]
        if datetime.now() - cached_at < _CACHE_TTL:
            return pressure
        else:
            del _weather_cache[city]
    return None


def _set_cached_pressure(city: str, pressure: int) -> None:
    _weather_cache[city] = (pressure, datetime.now())


def fetch_atmospheric_pressure_mmhg(city: str = "Київ") -> Optional[int]:
    """Отримати поточний атмосферний тиск (мм рт. ст.) через Open-Meteo API з кешуванням."""
    # Спробувати отримати з кешу
    cached = _get_cached_pressure(city)
    if cached is not None:
        return cached
    
    # Отримати з API
    coords = CITIES.get(city, CITIES["Київ"])
    lat, lon = coords
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current=surface_pressure"
    )
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        hpa = data.get("current", {}).get("surface_pressure")
        if hpa is None:
            return None
        pressure = int(round(float(hpa) * 0.75006))
        
        # Зберегти в кеш
        _set_cached_pressure(city, pressure)
        
        return pressure
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
        return None


def clear_weather_cache() -> None:
    """Очистити кеш погодних даних."""
    _weather_cache.clear()
```

**Перевірка:** Двічі викликати `fetch_atmospheric_pressure_mmhg()` для одного міста - другий виклик має повернути кешовані дані.

---

### Step 3.2: Додати retry logic для Weather API

**Проблема:** Немає retry logic при помилках API.

**Рішення:** Додати exponential backoff retry.

**Файл:** `app/weather.py`

**Дії:**
1. Додати retry decorator:
```python
import time

def retry_on_error(max_retries: int = 3, initial_delay: float = 1.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = initial_delay * (2 ** attempt)  # Exponential backoff
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


@retry_on_error(max_retries=3, initial_delay=1.0)
def fetch_atmospheric_pressure_mmhg(city: str = "Київ") -> Optional[int]:
    # ... існуючий код ...
```

**Перевірка:** Симулювати помилку API (відключити інтернет) - має бути 3 спроби з затримкою.

---

### Step 3.3: Додати pagination для measurements

**Проблема:** Завантажуються всі записи, проблеми з великими datasets.

**Рішення:** Додати pagination до repository.

**Файл:** `app/repositories/measurement_repository.py`

**Дії:**
1. Додати pagination методи:
```python
from typing import List, Optional, Tuple

class MeasurementRepository:
    # ... існуючий код ...
    
    def find_by_user_id_paginated(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Measurement], int]:
        """
        Отримати вимірювання з pagination.
        Повертає (measurements, total_count).
        """
        with db_cursor() as cur:
            # Отримати total count
            cur.execute(
                """
                SELECT COUNT(*) FROM measurements
                WHERE user_id = %s AND deleted_at IS NULL
                """,
                (user_id,),
            )
            total_count = cur.fetchone()[0]
            
            # Отримати дані для сторінки
            offset = (page - 1) * page_size
            cur.execute(
                """
                SELECT id, timestamp, systolic, diastolic, pulse, mood, notes,
                       atmospheric_pressure, medication_taken, activity_level
                FROM measurements
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, page_size, offset),
            )
            rows = cur.fetchall()
        
        measurements = [_row_to_measurement(row) for row in rows]
        return measurements, total_count
```

2. Оновити UI для підтримки pagination (опціонально для Phase 4).

**Перевірка:** Викликати `find_by_user_id_paginated()` з різними page numbers.

---

### Step 3.4: Додати doctor-patient assignment

**Проблема:** Лікарі бачать всіх пацієнтів, немає механізму прив'язки.

**Рішення:** Створити doctor-patient relationship table.

**Файл:** `migrations/005_doctor_patient_assignment.sql` (новий)
```sql
-- Таблиця прив'язки пацієнтів до лікарів
CREATE TABLE IF NOT EXISTS doctor_patient_assignments (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(id),
    UNIQUE(doctor_id, patient_id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_doctor ON doctor_patient_assignments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_assignments_patient ON doctor_patient_assignments(patient_id);
```

**Файл:** `app/repositories/assignment_repository.py` (новий)
```python
from __future__ import annotations

from typing import List

from app.auth import User, _row_to_user
from app.database import db_cursor


class AssignmentRepository:
    def assign_patient_to_doctor(
        self,
        doctor_id: int,
        patient_id: int,
        assigned_by: int,
    ) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO doctor_patient_assignments (doctor_id, patient_id, assigned_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (doctor_id, patient_id) DO NOTHING
                """,
                (doctor_id, patient_id, assigned_by),
            )
    
    def remove_assignment(self, doctor_id: int, patient_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "DELETE FROM doctor_patient_assignments WHERE doctor_id = %s AND patient_id = %s",
                (doctor_id, patient_id),
            )
    
    def get_doctor_patients(self, doctor_id: int) -> List[User]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.username, u.password_hash, u.full_name, u.role, u.age,
                       u.target_systolic, u.target_diastolic, u.target_pulse, u.is_active, u.email
                FROM users u
                INNER JOIN doctor_patient_assignments dpa ON u.id = dpa.patient_id
                WHERE dpa.doctor_id = %s AND u.deleted_at IS NULL
                ORDER BY u.full_name
                """,
                (doctor_id,),
            )
            rows = cur.fetchall()
        return [_row_to_user(r) for r in rows]
    
    def get_patient_doctors(self, patient_id: int) -> List[User]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.username, u.password_hash, u.full_name, u.role, u.age,
                       u.target_systolic, u.target_diastolic, u.target_pulse, u.is_active, u.email
                FROM users u
                INNER JOIN doctor_patient_assignments dpa ON u.id = dpa.doctor_id
                WHERE dpa.patient_id = %s AND u.deleted_at IS NULL
                ORDER BY u.full_name
                """,
                (patient_id,),
            )
            rows = cur.fetchall()
        return [_row_to_user(r) for r in rows]
```

**Перевірка:** Створити assignment, перевірити що лікар бачить тільки своїх пацієнтів.

---

## Phase 4: Production readiness (Priority: P2)

### Step 4.1: Додати structured logging

**Проблема:** Немає logging.

**Рішення:** Додати Python logging configuration.

**Файл:** `app/logging_config.py` (новий)
```python
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_dir: Path | None = None) -> None:
    """Налаштувати structured logging."""
    
    # Створити log directory якщо вказано
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"bp_monitor_{datetime.now().strftime('%Y%m%d')}.log"
    else:
        log_file = None
    
    # Формат логів
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Конфігурація
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Видалити існуючі handlers
    root_logger.handlers.clear()
    
    # Додати нові handlers
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Зменшити noise від external libraries
    logging.getLogger("PyQt6").setLevel(logging.WARNING)
    logging.getLogger("psycopg2").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Отримати logger для модуля."""
    return logging.getLogger(name)
```

**Файл:** `main.py` - ініціалізувати logging при startup:
```python
from app.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

if __name__ == '__main__':
    setup_logging(log_level="INFO", log_dir=Path("logs"))
    logger.info("Starting PulseView application")
    
    try:
        from app.main_window import run_app
        run_app()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise
```

**Додати logging в key modules:**

**Файл:** `app/database.py`
```python
from app.logging_config import get_logger

logger = get_logger(__name__)

def connect() -> PgConnection:
    try:
        logger.debug(f"Connecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        conn = psycopg2.connect(...)
        logger.info("Successfully connected to PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise
```

**Файл:** `app/auth.py`
```python
from app.logging_config import get_logger

logger = get_logger(__name__)

class AuthService:
    def login(self, username: str, password: str) -> Optional[User]:
        logger.info(f"Login attempt for user: {username}")
        # ... код ...
        if not row or not _verify_password(password, row[2]):
            logger.warning(f"Failed login attempt for user: {username}")
            return None
        logger.info(f"Successful login for user: {username}")
        return _row_to_user(row)
```

**Перевірка:** Запустити застосунок, перевірити що логи створюються в `logs/` directory.

---

### Step 4.2: Environment-first configuration

**Проблема:** Hardcoded defaults, немає environment variables.

**Рішення:** Пріоритет environment variables над config file.

**Файл:** `app/config.py` - оновити:
```python
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Dict

CONFIG_FILE = Path(__file__).parent.parent / "config.ini"

_DEFAULTS: Dict[str, str] = {
    "host": "localhost",
    "port": "5432",
    "database": "bp_monitor",
    "user": "postgres",
    "password": "postgres",
}


def _load_env() -> Dict[str, str]:
    """Завантажити конфігурацію з environment variables."""
    return {
        "host": os.getenv("DB_HOST", ""),
        "port": os.getenv("DB_PORT", ""),
        "database": os.getenv("DB_NAME", ""),
        "user": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def _load_ini() -> Dict[str, str]:
    """Завантажити конфігурацію з config.ini."""
    if not CONFIG_FILE.exists():
        return {}
    parser = ConfigParser()
    parser.read(CONFIG_FILE, encoding="utf-8")
    if not parser.has_section("database"):
        return {}
    section = parser["database"]
    return {key: section.get(key, fallback="").strip() for key in _DEFAULTS}


def _build_db_config() -> Dict[str, str]:
    """Побудувати конфігурацію з пріоритетом: ENV > INI > DEFAULTS."""
    env_config = _load_env()
    ini_config = _load_ini()
    
    return {
        "host": env_config["host"] or ini_config.get("host") or _DEFAULTS["host"],
        "port": env_config["port"] or ini_config.get("port") or _DEFAULTS["port"],
        "database": env_config["database"] or ini_config.get("database") or _DEFAULTS["database"],
        "user": env_config["user"] or ini_config.get("user") or _DEFAULTS["user"],
        "password": env_config["password"] or ini_config.get("password") or _DEFAULTS["password"],
    }


DB_CONFIG = _build_db_config()


def validate_config() -> None:
    """Валідувати конфігурацію при startup."""
    required_fields = ["host", "port", "database", "user", "password"]
    missing = [field for field in required_fields if not DB_CONFIG.get(field)]
    
    if missing:
        raise ValueError(
            f"Missing required database configuration fields: {', '.join(missing)}. "
            f"Set them via environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) "
            f"or config.ini file."
        )


def get_db_url() -> str:
    """Отримати URL для підключення до PostgreSQL."""
    return (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
```

**Файл:** `main.py` - додати валідацію:
```python
from app.config import validate_config

if __name__ == '__main__':
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    setup_logging(log_level="INFO", log_dir=Path("logs"))
    # ... решта коду ...
```

**Файл:** `.env.example` (новий)
```ini
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bp_monitor
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

**Перевірка:** Запустити з environment variables, переконатися що вони мають пріоритет.

---

### Step 4.3: Глобальний exception handler

**Проблема:** Немає централізованої обробки помилок.

**Рішення:** Додати global exception handler.

**Файл:** `app/exceptions.py` (новий)
```python
from __future__ import annotations

class BPMonitorError(Exception):
    """Базовий exception для застосунку."""
    pass


class ValidationError(BPMonitorError):
    """Помилка валідації даних."""
    pass


class AuthenticationError(BPMonitorError):
    """Помилка аутентифікації."""
    pass


class AuthorizationError(BPMonitorError):
    """Помилка авторизації."""
    pass


class DatabaseError(BPMonitorError):
    """Помилка бази даних."""
    pass


class ExternalServiceError(BPMonitorError):
    """Помилка зовнішнього сервісу (наприклад, weather API)."""
    pass
```

**Файл:** `main.py` - додати global exception handler:
```python
from app.exceptions import BPMonitorError
from app.logging_config import get_logger

logger = get_logger(__name__)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Глобальний handler для uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.error(
        f"Uncaught exception: {exc_type.__name__}: {exc_value}",
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    
    # Показати user-friendly message
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.critical(
        None,
        "Помилка",
        f"Сталася неочікувана помилка: {exc_value}\n"
        f"Деталі записано в лог-файл."
    )

if __name__ == '__main__':
    # Встановити global exception handler
    sys.excepthook = handle_exception
    
    try:
        validate_config()
        setup_logging(log_level="INFO", log_dir=Path("logs"))
        logger.info("Starting PulseView application")
        
        from app.main_window import run_app
        run_app()
    except BPMonitorError as e:
        logger.error(f"Application error: {e}", exc_info=True)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Помилка застосунку", str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
```

**Перевірка:** Спровокувати помилку, переконатися що вона логується і показується користувачу.

---

### Step 4.4: Automated backup strategy

**Проблема:** Тільки manual export, немає автоматичних бекапів.

**Рішення:** Додати automated backup service.

**Файл:** `app/services/backup_service.py` (новий)
```python
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import DB_CONFIG
from app.logging_config import get_logger

logger = get_logger(__name__)


class BackupService:
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, name: Optional[str] = None) -> Path:
        """Створити backup бази даних."""
        if name is None:
            name = f"bp_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
        
        backup_path = self.backup_dir / name
        
        # Використовувати pg_dump для backup
        cmd = [
            "pg_dump",
            f"--host={DB_CONFIG['host']}",
            f"--port={DB_CONFIG['port']}",
            f"--username={DB_CONFIG['user']}",
            f"--dbname={DB_CONFIG['database']}",
            f"--file={backup_path}",
            "--format=custom",
        ]
        
        # Встановити PGPASSWORD environment variable
        import os
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_CONFIG["password"]
        
        try:
            logger.info(f"Creating backup: {backup_path}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                raise RuntimeError(f"Backup failed: {result.stderr}")
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup error: {e}")
            raise
    
    def restore_backup(self, backup_path: Path) -> None:
        """Відновити базу даних з backup."""
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        cmd = [
            "pg_restore",
            f"--host={DB_CONFIG['host']}",
            f"--port={DB_CONFIG['port']}",
            f"--username={DB_CONFIG['user']}",
            f"--dbname={DB_CONFIG['database']}",
            str(backup_path),
        ]
        
        import os
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_CONFIG["password"]
        
        try:
            logger.info(f"Restoring backup: {backup_path}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                raise RuntimeError(f"Restore failed: {result.stderr}")
            
            logger.info(f"Backup restored successfully: {backup_path}")
        except Exception as e:
            logger.error(f"Restore error: {e}")
            raise
    
    def cleanup_old_backups(self, keep_days: int = 30) -> None:
        """Видалити старі бекапи."""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for backup_file in self.backup_dir.glob("*.backup"):
            if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                logger.info(f"Deleting old backup: {backup_file}")
                backup_file.unlink()
    
    def list_backups(self) -> list[Path]:
        """Отримати список всіх бекапів."""
        return sorted(self.backup_dir.glob("*.backup"), reverse=True)
```

**Файл:** `scripts/scheduled_backup.py` (новий)
```python
"""
Скрипт для запланованих бекапів.
Може бути запущений через cron або Windows Task Scheduler.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.backup_service import BackupService
from app.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging(log_level="INFO", log_dir=ROOT / "logs")
    
    backup_service = BackupService(ROOT / "backups")
    
    try:
        # Створити бекап
        backup_path = backup_service.create_backup()
        print(f"Backup created: {backup_path}")
        
        # Видалити старі бекапи (старші 30 днів)
        backup_service.cleanup_old_backups(keep_days=30)
        
    except Exception as e:
        print(f"Backup failed: {e}")
        sys.exit(1)
```

**Перевірка:** Запустити `python scripts/scheduled_backup.py`, перевірити що бекап створюється в `backups/` directory.

---

## Phase 5: Додаткові покращення (Priority: P3)

### Step 5.1: Додати більше unit тестів

**Файл:** `tests/test_measurement_service.py` (новий)
```python
import pytest
from unittest.mock import Mock
from app.services.measurement_service import MeasurementService
from app.storage import Measurement


def test_create_measurement_valid():
    mock_storage = Mock()
    service = MeasurementService(mock_storage)
    
    measurement = service.create_measurement(
        timestamp="2024-01-01 10:00",
        systolic=120,
        diastolic=80,
        pulse=72,
        mood="Спокійний",
        notes="",
        atmospheric_pressure=745,
        medication_taken=False,
        activity_level="Низька",
    )
    
    assert measurement.systolic == 120
    assert measurement.diastolic == 80
    mock_storage.add_measurement.assert_called_once()


def test_create_measurement_invalid_systolic():
    mock_storage = Mock()
    service = MeasurementService(mock_storage)
    
    with pytest.raises(ValueError, match="Валідація не пройшла"):
        service.create_measurement(
            timestamp="2024-01-01 10:00",
            systolic=50,  # Некоректне значення
            diastolic=80,
            pulse=72,
            mood="Спокійний",
            notes="",
            atmospheric_pressure=745,
            medication_taken=False,
            activity_level="Низька",
        )
```

---

### Step 5.2: Додати integration тести

**Файл:** `tests/integration/test_measurement_repository.py` (новий)
```python
import pytest
from app.repositories.measurement_repository import MeasurementRepository
from app.storage import Measurement
from app.auth import _hash_password
from app.database import db_cursor


@pytest.fixture
def test_user():
    """Створити тестового користувача."""
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role, age)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            ("test_user", _hash_password("TestPass123"), "Test User", "patient", 30),
        )
        user_id = cur.fetchone()[0]
    
    yield user_id
    
    # Cleanup
    with db_cursor() as cur:
        cur.execute("DELETE FROM measurements WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))


def test_save_and_find_measurement(test_user):
    repo = MeasurementRepository()
    
    measurement = Measurement(
        id="test123",
        timestamp="2024-01-01 10:00",
        systolic=120,
        diastolic=80,
        pulse=72,
        mood="Спокійний",
        notes="",
        atmospheric_pressure=745,
        medication_taken=False,
        activity_level="Низька",
    )
    
    repo.save(measurement, test_user)
    
    measurements = repo.find_by_user_id(test_user)
    assert len(measurements) == 1
    assert measurements[0].systolic == 120
```

---

### Step 5.3: Додати UI тести

**Файл:** `tests/ui/test_measurements_page.py` (новий)
```python
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from app.ui.measurements_page import MeasurementsPage


@pytest.fixture
def app(qtbot):
    """Fixture для PyQt6 application."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    yield application


def test_add_measurement(app, qtbot):
    """Тест додавання вимірювання через UI."""
    add_callback = Mock()
    delete_callback = Mock()
    
    page = MeasurementsPage(add_callback, delete_callback)
    qtbot.addWidget(page)
    
    # Заповнити форму
    page.systolic_spin.setValue(120)
    page.diastolic_spin.setValue(80)
    page.pulse_spin.setValue(72)
    
    # Клікнути кнопку "Зберегти запис"
    QTest.mouseClick(page.add_btn, Qt.MouseButton.LeftButton)
    
    # Перевірити що callback був викликаний
    add_callback.assert_called_once()
```

---

## CHECKLIST ПЕРЕД PRODUCTION

### Безпека
- [ ] Password policy: 8+ chars, complexity requirements
- [ ] Connection pooling реалізовано
- [ ] SQL injection protection (parameterized queries)
- [ ] Soft delete замість cascade delete
- [ ] Server-side validation
- [ ] Environment variables для secrets
- [ ] Logging sensitive operations

### Архітектура
- [ ] Service layer створено
- [ ] Repository pattern реалізовано
- [ ] UI розділено на окремі файли
- [ ] DTO layer (опціонально для desktop)
- [ ] Dependency injection (опціонально)

### Функціональність
- [ ] Weather API з caching та retry logic
- [ ] Pagination для великих datasets
- [ ] Doctor-patient assignment
- [ ] Soft delete mechanism
- [ ] Automated backup strategy

### Тестування
- [ ] Unit тести для analytics
- [ ] Unit тести для validation
- [ ] Unit тести для services
- [ ] Integration тести для repositories
- [ ] UI тести (опціонально)
- [ ] Coverage > 70%

### Observability
- [ ] Structured logging
- [ ] Log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Audit logging для critical operations
- [ ] Error tracking

### Configuration
- [ ] Environment-first configuration
- [ ] Config validation при startup
- [ ] .env.example файл
- [ ] Documentation для deployment

### Performance
- [ ] Connection pooling
- [ ] Pagination
- [ ] Caching для external APIs
- [ ] Indexes в БД

---

## РЕЗУЛЬТАТ

Після виконання всіх Phase 1-4 система буде мати:

**Production readiness: 8.5/10**

**Досягнення:**
- ✅ Connection pooling
- ✅ Strong password policy
- ✅ Soft delete
- ✅ Server-side validation
- ✅ Service layer
- ✅ Repository pattern
- ✅ Structured logging
- ✅ Environment configuration
- ✅ Automated backups
- ✅ Unit та integration тести
- ✅ Weather API з caching/retry
- ✅ Pagination
- ✅ Doctor-patient assignment

**Що залишається для 10/10:**
- Dependency injection container
- Comprehensive UI тести
- Performance optimization
- Load testing
- Security audit
- Documentation для end users
- Installation wizard
- Auto-updater

---

## ЗАГАЛЬНІ РЕКОМЕНДАЦІЇ

1. **Виконувати Phase по порядку:** Не переходити до Phase 2 поки Phase 1 не завершено.
2. **Тести після кожного Step:** Писати тести одразу після реалізації функціональності.
3. **Code review:** Робити code review після кожного Phase.
4. **Documentation:** Документувати зміни в README.md.
5. **Git commits:** Робити окремі commits для кожного Step.
6. **Backup:** Робити backup бази даних перед кожною міграцією.
7. **Testing environment:** Мати окрему test database.

---

## ЧАСОВІ ОЦІНКИ

- **Phase 1 (Critical fixes):** 2-3 дні
- **Phase 2 (Architecture):** 5-7 днів
- **Phase 3 (Features):** 3-4 дні
- **Phase 4 (Production):** 3-4 дні
- **Phase 5 (Enhancements):** 2-3 дні

**Всього:** 15-21 день для одного розробника.

---

## КОНТАКТИ ТА РЕСУРСИ

- PostgreSQL: https://www.postgresql.org/docs/
- PyQt6: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- psycopg2: https://www.psycopg.org/docs/
- pytest: https://docs.pytest.org/

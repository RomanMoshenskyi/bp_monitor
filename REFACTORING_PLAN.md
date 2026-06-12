# План трансформації коду відповідно до дипломного опису

## Архітектурний підхід

- **Зберігаємо:** Desktop PyQt6 + PostgreSQL + SQLAlchemy ORM
- **З диплому беремо:** Domain Models, Service Layer, Access Control, Audit, Business Logic
- **НЕ робимо:** REST API, JWT, HTTP сервер (бо це desktop)
- **ЗАМІНЮЄМО:** Внутрішній Service Layer з DI контейнером

---

## Phase 1: Foundation — SQLAlchemy ORM (Тиждень 1)

### Step 1.1: Додати SQLAlchemy

```bash
# requirements.txt - додати:
SQLAlchemy>=2.0
alembic>=1.12
```

### Step 1.2: Створити ORM Base

**Файл:** `app/infrastructure/orm/base.py`
```python
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from app.config import get_db_url

class Base(DeclarativeBase):
    pass

engine = create_engine(get_db_url(), pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Step 1.3: Alembic міграції

```bash
cd d:\Downloads\bp_monitor-main
alembic init migrations_alembic
```

Налаштувати `alembic/env.py` для підключення `Base`

### Step 1.4: Створити Alembic міграцію з усіма таблицями

```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

### Step 1.5: Міграція зі старої схеми ⭐ NEW

**Завдання:** Перенести дані з поточної схеми (psycopg2) у нову (SQLAlchemy ORM).

**Файл:** `scripts/migrate_from_legacy.py`

```python
"""Скрипт для міграції даних зі старої схеми у нову ORM схему."""

def migrate_users():
    """Перенести користувачів."""
    
def migrate_measurements():
    """Перенести вимірювання (зв'язати з WeatherSnapshot)."""
    
def main():
    # 1. Зчитати всі дані зі старих таблиць
    # 2. Конвертувати у нові ORM моделі
    # 3. Зберегти у нові таблиці
    pass
```

---

## Phase 2: Domain Layer — Моделі з диплому (Тиждень 2)

### Step 2.0: Оновити моделі додати relationships

Створити таблиці:
- `users` (розширена)
- `measurements`
- `medications` ⭐ NEW
- `medication_intakes` ⭐ NEW
- `activity_events` ⭐ NEW
- `weather_snapshots` ⭐ NEW
- `threshold_profiles` ⭐ NEW
- `daily_summaries` ⭐ NEW
- `audit_logs` ⭐ NEW
- `doctor_patient_assignments` (оновити)

---

## Phase 2: Domain Layer — Моделі з диплому (Тиждень 2)

### Step 2.1: User ORM

**Файл:** `app/domain/entities/user.py`

Атрибути з диплому:
- `id`, `username`, `email`, `email_verified` ⭐
- `password_hash`, `full_name`, `role`, `age`
- `target_systolic`, `target_diastolic`, `target_pulse`
- `is_active`, `deleted_at` (soft delete)
- Relationships: `measurements`, `threshold_profile`, `assigned_doctors`

### Step 2.2: Measurement ORM

**Файл:** `app/domain/entities/measurement.py`

Атрибути:
- `id`, `user_id`, `timestamp`, `systolic`, `diastolic`, `pulse`
- `mood`, `notes`
- `location_lat`, `location_lon` ⭐ (геокоординати з диплому)
- `weather_snapshot_id` → `weather_snapshot` relationship ⭐
- `medication_intakes` relationship ⭐
- `activity_events` relationship ⭐

### Step 2.3: WeatherSnapshot ⭐ NEW

**Файл:** `app/domain/entities/weather.py`

```python
class WeatherSnapshotORM(Base):
    __tablename__ = "weather_snapshots"
    
    id = Column(Integer, primary_key=True)
    city_name = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    atmospheric_pressure_hpa = Column(Float)
    atmospheric_pressure_mmhg = Column(Integer)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    fetched_at = Column(DateTime, server_default=func.now())
    
    measurements = relationship("MeasurementORM", back_populates="weather_snapshot")
```

### Step 2.4: Medication + MedicationIntake ⭐ NEW

**Файл:** `app/domain/entities/medication.py`

```python
class MedicationORM(Base):
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    form = Column(String(50))  # таблетки, капсули...
    dosage_unit = Column(String(20))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    intakes = relationship("MedicationIntakeORM", back_populates="medication")


class MedicationIntakeORM(Base):
    __tablename__ = "medication_intakes"
    
    id = Column(Integer, primary_key=True)
    medication_id = Column(Integer, ForeignKey("medications.id"))
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True)
    taken_at = Column(DateTime, nullable=False)
    dosage = Column(String(50))
    
    medication = relationship("MedicationORM", back_populates="intakes")
    measurement = relationship("MeasurementORM", back_populates="medication_intakes")
```

### Step 2.5: ActivityEvent ⭐ NEW

**Файл:** `app/domain/entities/activity.py`

```python
class ActivityEventORM(Base):
    __tablename__ = "activity_events"
    
    id = Column(Integer, primary_key=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True)
    activity_type = Column(String(50))  # біг, ходьба...
    intensity_level = Column(String(20))
    duration_minutes = Column(Integer)
    recorded_at = Column(DateTime, nullable=False)
    notes = Column(Text)
    
    measurement = relationship("MeasurementORM", back_populates="activity_events")
```

### Step 2.6: ThresholdProfile ⭐ NEW

**Файл:** `app/domain/entities/threshold.py`

```python
class ThresholdProfileORM(Base):
    __tablename__ = "threshold_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    systolic_min = Column(Integer, default=90)
    systolic_max = Column(Integer, default=140)
    diastolic_min = Column(Integer, default=60)
    diastolic_max = Column(Integer, default=90)
    pulse_min = Column(Integer, default=50)
    pulse_max = Column(Integer, default=100)
    alerts_enabled = Column(Boolean, default=True)
    
    user = relationship("UserORM", back_populates="threshold_profile")
```

### Step 2.7: DailySummary ⭐ NEW

**Файл:** `app/domain/entities/daily_summary.py`

```python
class DailySummaryORM(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    summary_date = Column(Date, nullable=False)
    
    avg_systolic = Column(Float)
    min_systolic = Column(Integer)
    max_systolic = Column(Integer)
    avg_diastolic = Column(Float)
    min_diastolic = Column(Integer)
    max_diastolic = Column(Integer)
    avg_pulse = Column(Float)
    measurements_count = Column(Integer)
    
    __table_args__ = (UniqueConstraint('user_id', 'summary_date'),)
```

### Step 2.8: Recommendation ⭐ NEW (з діаграми класів диплому)

**Файл:** `app/domain/entities/recommendation.py`

```python
class RecommendationORM(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True)
    
    severity = Column(String(20))  # low, medium, high, critical
    message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    patient = relationship("UserORM", back_populates="recommendations")
    measurement = relationship("MeasurementORM", back_populates="recommendations")
```

### Step 2.9: AuditLogEntry ⭐ NEW (з діаграми класів диплому)

**Файл:** `app/domain/entities/audit_log.py`

```python
class AuditLogEntryORM(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))  # measurement_created, login, etc.
    details = Column(Text)  # JSON string
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    
    user = relationship("UserORM")
```

### Step 2.10: Report ⭐ NEW (з діаграми класів диплому)

**Файл:** `app/domain/entities/report.py`

```python
class ReportORM(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    period_start = Column(Date)
    period_end = Column(Date)
    file_path = Column(String(255))
    file_format = Column(String(10))  # pdf, csv, json
    created_at = Column(DateTime, server_default=func.now())
    
    patient = relationship("UserORM", back_populates="reports")
```

---

## Phase 3: Application Layer — Сервіси (Тиждень 3)

### Step 3.1: MonitoringService ⭐ (з діаграми класів диплому)

**Файл:** `app/application/services/monitoring_service.py`

Методи:
- `add_measurement(dto, current_user)` — з погодою та аудитом
- `get_patient_history(doctor, patient_id, period)` — з перевіркою assignment
- `update_daily_summary(user_id, date)`

### Step 3.2: AnalysisService

**Файл:** `app/application/services/analysis_service.py`

Методи:
- `evaluate(measurement, profile)` → `AnalysisResult`
- `calculate_correlation(bp_list, atm_list)` — формула Пірсона
- `generate_recommendations(measurement, status)`

### Step 3.3: WeatherService

**Файл:** `app/infrastructure/external/weather_service.py`

```python
class WeatherService:
    def __init__(self, provider, cache, repo):
        self._provider = provider
        self._cache = cache
        self._repo = repo
    
    def get_for_city(self, city: str) -> Optional[WeatherSnapshot]:
        # 1. Перевірити кеш
        # 2. Викликати API (Open-Meteo)
        # 3. Зберегти в БД та кеш
        # 4. Повернути WeatherSnapshot
```

### Step 3.4: AccessControl ⭐ NEW (з диплому)

**Файл:** `app/infrastructure/security/access_control.py`

```python
class AccessControl:
    """RBAC: canRead, canWrite з діаграми класів диплому"""
    
    def can_read_patient_data(self, doctor: User, patient_id: int) -> bool:
        """Лікар читає тільки своїх пацієнтів."""
        
    def can_write_measurements(self, user: User, target_user_id: int) -> bool:
        """Пацієнт пише тільки свої дані."""
```

### Step 3.5: AuditService ⭐ NEW (з диплому)

**Файл:** `app/infrastructure/security/audit_service.py`

```python
class AuditService:
    """log(userId, action, details) з діаграми класів диплому"""
    
    def log(self, user_id: int, action: str, details: Dict, ip_address: str = None):
        # Зберегти в audit_logs таблицю
        
    def get_user_actions(self, user_id: int, limit: int = 100) -> List[AuditLogEntry]:
        # Отримати історію дій
```

### Step 3.6: RecommendationService ⭐ NEW (з діаграми класів диплому)

**Файл:** `app/application/services/recommendation_service.py`

```python
class RecommendationService:
    """Генерація рекомендацій (з класу Recommendation диплому)."""
    
    def __init__(self, recommendation_repo: RecommendationRepository):
        self._repo = recommendation_repo
    
    def generate(
        self, 
        measurement: Measurement, 
        analysis: AnalysisResult,
        profile: ThresholdProfile
    ) -> List[Recommendation]:
        """Створити персоналізовані рекомендації на основі аналізу."""
        
    def get_for_patient(self, patient_id: int, limit: int = 50) -> List[Recommendation]:
        """Отримати історію рекомендацій пацієнта."""
```

### Step 3.7: ReportService ⭐ NEW (з діаграми класів диплому)

**Файл:** `app/application/services/report_service.py`

```python
class ReportService:
    """Генерація звітів (PDF, CSV) з діаграми класів диплому."""
    
    def __init__(self, report_repo: ReportRepository, pdf_generator: PDFGenerator):
        self._repo = report_repo
        self._pdf = pdf_generator
    
    def generate_pdf(self, patient_id: int, period: DateRange) -> Report:
        """Звіт у PDF форматі."""
        
    def generate_csv(self, patient_id: int, measurements: List[Measurement]) -> Report:
        """Експорт у CSV."""
        
    def list_for_patient(self, patient_id: int) -> List[Report]:
        """Список згенерованих звітів."""
```

---

## Phase 4: DTO Layer (2-3 дні)

### Step 4.1: DTO з діаграми класів диплому

**Файли:**
- `app/application/dto/measurement_dto.py`
- `app/application/dto/user_dto.py`
- `app/application/dto/threshold_dto.py`
- `app/application/dto/weather_dto.py`
- `app/application/dto/analysis_dto.py`
- `app/application/dto/medication_dto.py` ⭐
- `app/application/dto/activity_dto.py` ⭐
- `app/application/dto/recommendation_dto.py` ⭐
- `app/application/dto/report_dto.py` ⭐

---

## Phase 5: UI Layer — ViewModels (1.5 тижня)

### Step 5.1: DashboardViewModel

**Файл:** `app/presentation/view_models/dashboard_view_model.py`

```python
class DashboardViewModel(QObject):
    data_loaded = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, monitoring_service: MonitoringService, current_user: User):
        self._service = monitoring_service
        self._user = current_user
    
    def load_data(self, period_days: int = 30):
        self._measurements = self._service.get_history(...)
        self.data_loaded.emit()
    
    def get_statistics(self) -> StatisticsDTO:
        return self._service.calculate_statistics(self._measurements)
```

### Step 5.2: Рефакторинг UI сторінок

Сторінки оновити:
- `DashboardPage` — використовує `DashboardViewModel`
- `MeasurementsPage` — використовує `MeasurementsViewModel`
- `AnalyticsPage` — використовує `AnalyticsViewModel`
- `SettingsPage` — використовує `SettingsViewModel`

### Step 5.3: DoctorAssignmentDialog ⭐ NEW

**Файл:** `app/presentation/ui/doctor_assignment_dialog.py`

UI для призначення лікаря пацієнту (з диплому).

### Step 5.4: RecommendationsPage ⭐ NEW (з діаграми класів диплому)

**Файл:** `app/presentation/ui/recommendations_page.py`

```python
class RecommendationsPage(QWidget):
    """Сторінка перегляду рекомендацій пацієнта (з диплому)."""
    
    def __init__(self, view_model: RecommendationsViewModel):
        self._vm = view_model
```

### Step 5.5: ViewModels для всіх сторінок

- `DashboardViewModel`
- `MeasurementsViewModel`
- `AnalyticsViewModel`
- `SettingsViewModel`
- `RecommendationsViewModel` ⭐ NEW

---

## Phase 6: Infrastructure (Тиждень 6)

### Step 6.1: Email Verification ⭐ NEW

**Файли:**
- `app/infrastructure/external/email_service.py` — SMTP/SendGrid
- `app/application/services/verification_service.py` — токени

### Step 6.2: Encryption Service ⭐ NEW

**Файл:** `app/infrastructure/security/encryption.py`

Для шифрування бекапів (з диплому).

### Step 6.3: Backup Service (оновити)

**Файл:** `app/application/services/backup_service.py`

Додати шифрування та автоматичне резервування.

---

## Phase 7: Integration & Testing (2 тижні)

### Step 7.1: Інтеграційні тести

**Файли:**
- `tests/integration/test_monitoring_service.py`
- `tests/integration/test_weather_service.py`
- `tests/integration/test_access_control.py`

Приклад:
```python
def test_add_measurement_with_weather_and_audit():
    user = create_test_user()
    dto = MeasurementDTO(systolic=120, ..., city="Київ")
    measurement = monitoring_service.add_measurement(dto, user)
    
    assert measurement.weather_snapshot is not None
    logs = audit_service.get_user_actions(user.id)
    assert any(log.action == "measurement_created" for log in logs)
```

### Step 7.2: E2E тести

**Файл:** `tests/e2e/test_measurement_flow.py`

```python
def test_user_creates_measurement(qtbot):
    app = create_test_app()
    login_page = app.open_login()
    login_page.enter_credentials("patient", "pass")
    # ... перевірка UI flow
```

---

## Phase 8: Final Polish (Тиждень 8)

### Step 8.1: DI Container

**Файл:** `app/di/container.py`

```python
class DIContainer:
    def __init__(self):
        # Repositories
        self.measurement_repo = MeasurementRepository(SessionLocal)
        # Services
        self.weather_service = WeatherService(...)
        self.monitoring_service = MonitoringService(...)
    
    def create_main_window(self, user: User) -> MainWindow:
        dashboard_vm = DashboardViewModel(self.monitoring_service, user)
        return MainWindow(dashboard_vm, ...)
```

### Step 8.2: Entry point

**Файл:** `app/main.py`

```python
def run_app():
    container = DIContainer()
    login = LoginDialog(container.auth_service)
    if not login.exec():
        return
    window = container.create_main_window(login.user)
    window.show()
```

---

## Timeline

| Phase | Тривалість | Результати |
|-------|-----------|------------|
| Phase 1 | 1 тиждень | SQLAlchemy ORM, Alembic |
| Phase 2 | 1 тиждень | 8 ORM-моделей |
| Phase 3 | 1 тиждень | Service Layer |
| Phase 4 | 2-3 дні | DTO layer |
| Phase 5 | 1.5 тижня | ViewModels, UI refactor |
| Phase 6 | 1 тиждень | Email, Backup |
| Phase 7 | 2 тижні | Integration & E2E tests |
| Phase 8 | 1 тиждень | DI, документація |

**Загалом: 8-9 тижнів (~2 місяці)**

---

## Чекліст реалізації з диплому

### Моделі (8 штук)
- [ ] UserORM (розширена)
- [ ] MeasurementORM (з weather_snapshot_id)
- [ ] WeatherSnapshotORM ⭐
- [ ] MedicationORM ⭐
- [ ] MedicationIntakeORM ⭐
- [ ] ActivityEventORM ⭐
- [ ] ThresholdProfileORM ⭐
- [ ] DailySummaryORM ⭐

### Сервіси
- [ ] MonitoringService (центральний)
- [ ] AnalysisService
- [ ] WeatherService
- [ ] AccessControl ⭐
- [ ] AuditService ⭐
- [ ] EmailVerificationService ⭐

### DTO
- [ ] MeasurementDTO
- [ ] UserDTO
- [ ] WeatherSnapshotDTO ⭐
- [ ] MedicationDTO ⭐
- [ ] ActivityEventDTO ⭐
- [ ] ThresholdProfileDTO ⭐
- [ ] DailySummaryDTO ⭐

### Інфраструктура
- [ ] EmailService ⭐
- [ ] EncryptionService ⭐
- [ ] DI Container

### UI
- [ ] DashboardViewModel
- [ ] MeasurementsViewModel
- [ ] AnalyticsViewModel
- [ ] DoctorAssignmentDialog ⭐

### Repositories (11 штук) ⭐ NEW
- [ ] MeasurementRepository
- [ ] UserRepository
- [ ] WeatherSnapshotRepository
- [ ] MedicationRepository
- [ ] MedicationIntakeRepository
- [ ] ActivityEventRepository
- [ ] ThresholdProfileRepository
- [ ] DailySummaryRepository
- [ ] RecommendationRepository
- [ ] AuditLogRepository
- [ ] ReportRepository

### Тести
- [ ] Integration tests (Monitoring + Weather + Audit + Recommendation)
- [ ] E2E tests (PyQt6 flow)
- [ ] Repository tests (11 repositories)

---

## Що НЕ робимо (бо desktop)

- ❌ REST API
- ❌ JWT токени
- ❌ HTTPS/TLS
- ❌ Redis (використовуємо in-memory cache)

## Що ОБОВ'ЯЗКОВО робимо з диплому

### Моделі (11 штук) ⭐ оновлено
- ✅ ВСІ 8 базових моделей
- ✅ RecommendationORM (з діаграми класів)
- ✅ AuditLogEntryORM (з діаграми класів)
- ✅ ReportORM (з діаграми класів)

### Сервіси (8 штук) ⭐ оновлено
- ✅ MonitoringService (центральний координатор)
- ✅ AnalysisService
- ✅ WeatherService
- ✅ AccessControl (RBAC)
- ✅ AuditService
- ✅ EmailVerificationService
- ✅ RecommendationService (з діаграми класів)
- ✅ ReportService (з діаграми класів)

### Repositories (11 штук) ⭐
- ✅ Всі repositories для ORM моделей

### DTO (9 штук) ⭐ оновлено
- ✅ Всі DTO включаючи RecommendationDTO та ReportDTO

### UI (5+ сторінок) ⭐ оновлено
- ✅ Всі сторінки з ViewModels
- ✅ DoctorAssignmentDialog
- ✅ RecommendationsPage (з діаграми класів)

### Інфраструктура
- ✅ Service Layer з DI
- ✅ Access Control (canRead/canWrite)
- ✅ Audit Logging
- ✅ Email Verification

---

## Контрольні точки

### Checkpoint 1 (кінець Phase 2)
- [ ] **11 ORM-моделей** створено (8 базових + Recommendation + AuditLogEntry + Report)
- [ ] Alembic міграції робочі
- [ ] Міграція зі старої схеми пройшла успішно
- [ ] `pytest tests/domain/` проходять

### Checkpoint 2 (кінець Phase 3)
- [ ] `MonitoringService` інтегровано
- [ ] `AccessControl` працює
- [ ] `AuditService` логує

### Checkpoint 3 (кінець Phase 5)
- [ ] Всі UI сторінки через ViewModels
- [ ] Doctor-Patient Assignment UI працює
- [ ] Email verification flow готовий

### Checkpoint 4 (кінець Phase 7)
- [ ] 90%+ покриття тестами
- [ ] E2E тести проходять
- [ ] Код відповідає діаграмі класів диплому

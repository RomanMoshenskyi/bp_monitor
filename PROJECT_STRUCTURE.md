# BP Monitor - Refactored Project Structure

## Clean Architecture (по диплому)

```
bp_monitor-main/
├── app/
│   ├── domain/
│   │   └── entities/              ← 11 ORM Models
│   │       ├── __init__.py
│   │       ├── user_orm.py        ← User, UserRole
│   │       ├── measurement_orm.py ← BloodPressureMeasurement
│   │       ├── weather_orm.py     ← WeatherSnapshot
│   │       ├── medication_orm.py  ← Medication, MedicationIntake
│   │       ├── activity_orm.py    ← ActivityEvent
│   │       ├── threshold_orm.py   ← ThresholdProfile
│   │       ├── daily_summary_orm.py
│   │       ├── recommendation_orm.py
│   │       ├── audit_log_orm.py ← AuditLogEntry
│   │       └── report_orm.py      ← Report
│   │
│   ├── application/
│   │   ├── dto/                   ← 12 DTOs
│   │   │   ├── __init__.py
│   │   │   ├── user_dto.py
│   │   │   ├── measurement_dto.py
│   │   │   ├── weather_dto.py
│   │   │   ├── analysis_dto.py    ← AnalysisResult, CorrelationResult
│   │   │   ├── recommendation_dto.py
│   │   │   └── report_dto.py
│   │   │
│   │   └── services/              ← 7 Services (з діаграми диплому)
│   │       ├── __init__.py
│   │       ├── monitoring_service.py  ← MonitoringService
│   │       ├── analysis_service.py    ← Pearson correlation
│   │       ├── audit_service.py       ← AuditService.log()
│   │       ├── recommendation_service.py
│   │       ├── report_service.py
│   │       ├── access_control.py      ← RBAC (canRead, canWrite)
│   │       └── weather_service.py
│   │
│   ├── infrastructure/
│   │   ├── orm/                   ← SQLAlchemy
│   │   │   ├── __init__.py
│   │   │   └── base.py            ← Base, engine, SessionLocal
│   │   │
│   │   └── external/
│   │       └── email_service.py   ← (placeholder)
│   │
│   ├── presentation/
│   │   └── view_models/           ← 4 ViewModels (MVVM)
│   │       ├── __init__.py
│   │       ├── base_view_model.py
│   │       ├── dashboard_view_model.py
│   │       ├── measurements_view_model.py
│   │       └── analytics_view_model.py
│   │
│   ├── repositories/              ← 5 Repositories
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── user_repository_orm.py
│   │   ├── measurement_repository_orm.py
│   │   ├── weather_repository.py
│   │   ├── recommendation_repository_orm.py
│   │   ├── assignment_repository.py
│   │   ├── user_repository.py    ← legacy
│   │   ├── measurement_repository.py ← legacy
│   │   └── recommendation_repository.py ← legacy
│   │
│   ├── ui/                        ← UI Pages
│   │   ├── __init__.py
│   │   ├── dashboard_page.py          ← legacy
│   │   ├── dashboard_page_refactored.py  ← NEW with ViewModel
│   │   ├── measurements_page.py       ← legacy
│   │   ├── measurements_page_refactored.py ← NEW with ViewModel
│   │   ├── analytics_page.py
│   │   ├── settings_page.py
│   │   └── ...
│   │
│   ├── di/                        ← Dependency Injection
│   │   └── container.py           ← (placeholder)
│   │
│   ├── auth.py                    ← legacy auth
│   ├── config.py                  ← configuration
│   ├── database.py                ← legacy psycopg2
│   ├── main_window.py             ← main window (legacy)
│   ├── models.py                  ← dataclass models
│   └── ...
│
├── migrations_alembic/              ← Alembic migrations
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema_3_tables.py
│       └── 002_all_11_tables.py
│
├── tests/                         ← Tests
│   ├── test_validation.py
│   ├── test_analytics.py
│   ├── test_measurement_service.py
│   └── ...
│
├── REFACTORING_PLAN.md            ← Original plan
├── PROJECT_STRUCTURE.md           ← This file
├── INTEGRATE_VIEWMODELS.md        ← Integration guide
├── APPLY_MIGRATION.md             ← Migration guide
├── requirements.txt               ← Dependencies
└── README.md
```

## Архітектура по шарам

### 1. Domain Layer (Entities)
- 11 ORM моделей з діаграми класів диплому
- SQLAlchemy declarative base
- Relationships між моделями

### 2. Application Layer (Services + DTOs)
- **7 Services** — бізнес-логіка
- **12 DTOs** — data transfer objects
- Pearson correlation formula (діплом 3.2)

### 3. Infrastructure Layer
- SQLAlchemy ORM
- Alembic migrations
- Connection pooling

### 4. Presentation Layer (MVVM)
- **4 ViewModels** — зв'язок між UI та Services
- PyQt6 signals для оновлення UI
- Pagination для великих даних

## Ключові компоненти диплому

| Компонент диплому | Реалізація |
|-------------------|------------|
| User, Patient, Doctor, Admin | `UserORM` з `UserRole` enum |
| BloodPressureMeasurement | `MeasurementORM` |
| AtmosphericPressureSample | `WeatherSnapshotORM` |
| Recommendation | `RecommendationORM` + `RecommendationService` |
| ThresholdProfile | `ThresholdProfileORM` |
| Report | `ReportORM` + `ReportService` |
| MonitoringService | `MonitoringService` — координатор |
| AnalysisService | `AnalysisService` — Pearson correlation |
| WeatherServiceClient | `WeatherService` + `weather.py` |
| AccessControl | `AccessControl` — RBAC |
| AuditService | `AuditService` — логування |

## Статус реалізації

| Phase | Статус | Компоненти |
|-------|--------|-----------|
| **Phase 1** | ✅ Complete | SQLAlchemy ORM, Alembic, 3 базові моделі |
| **Phase 2** | ✅ Complete | 11 ORM моделей, 5 Repositories |
| **Phase 3** | ✅ Complete | 7 Services, 12 DTOs |
| **Phase 4** | ✅ Complete | 4 ViewModels (MVVM) |
| **Phase 6** | ✅ Complete | UI Pages з ViewModel |
| **Phase 5** | ⏳ Optional | DI Container (можна додати пізніше) |
| **Phase 7** | ⏳ Optional | Integration/E2E тести |

## Що НЕ зроблено (з диплому, бо desktop app)

- ❌ REST API — не потрібно для desktop
- ❌ JWT tokens — не потрібно для desktop
- ❌ HTTPS/TLS — не потрібно для desktop
- ❌ Redis caching — використано in-memory

## Наступні кроки

1. **Застосувати міграції:**
   ```bash
   alembic -c migrations_alembic/alembic.ini upgrade head
   ```

2. **Інтегрувати ViewModels:**
   Див. `INTEGRATE_VIEWMODELS.md`

3. **Тестувати:**
   ```bash
   python -m pytest tests/ -v
   ```

4. **Перевірити кореляцію:**
   ```bash
   python -c "from app.application.services import AnalysisService; s = AnalysisService(); print(s.calculate_pearson_correlation([120,130,140], [750,760,770]))"
   ```

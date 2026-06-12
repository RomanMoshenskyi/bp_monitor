# Інструкція: Інтеграція ViewModels у MainWindow

## Огляд

Файли з інтеграцією ViewModel вже створені:
- `app/ui/dashboard_page_refactored.py` — Dashboard з ViewModel
- `app/ui/measurements_page_refactored.py` — Measurements з ViewModel та pagination

## Кроки інтеграції

### 1. Імпорти у main_window.py

Додай імпорти у верхній частині `main_window.py`:

```python
# ViewModels
from app.presentation.view_models import (
    DashboardViewModel,
    MeasurementsViewModel,
    AnalyticsViewModel,
)

# Refactored pages
from app.ui import DashboardPageRefactored, MeasurementsPageRefactored

# Services (для створення ViewModels)
from app.application.services import (
    MonitoringService,
    AnalysisService,
    AuditService,
    RecommendationService,
    ReportService,
    AccessControl,
    WeatherService,
)

# Repositories
from app.repositories import (
    UserRepositoryORM,
    MeasurementRepositoryORM,
    WeatherRepository,
    RecommendationRepositoryORM,
)

# SQLAlchemy session
from app.infrastructure.orm import SessionLocal
```

### 2. Створення ViewModels у MainWindow.__init__

Додай створення ViewModels після ініціалізації UI:

```python
def _init_view_models(self):
    """Initialize ViewModels with dependency injection."""
    # Create DB session
    self._db = SessionLocal()
    
    # Create repositories
    self._user_repo = UserRepositoryORM(self._db)
    self._measurement_repo = MeasurementRepositoryORM(self._db)
    self._weather_repo = WeatherRepository(self._db)
    self._recommendation_repo = RecommendationRepositoryORM(self._db)
    
    # Create services
    self._analysis_service = AnalysisService()
    self._audit_service = AuditService(self._db)
    self._recommendation_service = RecommendationService(self._db)
    self._report_service = ReportService(self._db)
    self._weather_service = WeatherService(self._db, self._weather_repo)
    
    self._monitoring_service = MonitoringService(
        db=self._db,
        measurement_repo=self._measurement_repo,
        user_repo=self._user_repo,
        weather_repo=self._weather_repo,
        analysis_service=self._analysis_service,
        audit_service=self._audit_service,
    )
    
    # Create ViewModels
    self._dashboard_vm = DashboardViewModel(
        current_user=self._current_user,
        monitoring_service=self._monitoring_service,
        analysis_service=self._analysis_service,
    )
    
    self._measurements_vm = MeasurementsViewModel(
        current_user=self._current_user,
        monitoring_service=self._monitoring_service,
        page_size=20,
    )
```

### 3. Оновлення _create_pages()

Заміни створення сторінок на ViewModel-версії:

```python
def _create_pages(self):
    """Create page widgets with ViewModels."""
    # Dashboard with ViewModel
    self._dashboard_page = DashboardPageRefactored(self._dashboard_vm)
    
    # Measurements with ViewModel
    self._measurements_page = MeasurementsPageRefactored(self._measurements_vm)
    
    # Analytics (можна залишити стару або оновити)
    self._analytics_page = AnalyticsPage()
    
    # Settings (можна залишити стару)
    self._settings_page = SettingsPage()
```

### 4. Оновлення сигналів при перемиканні користувача

Коли користувач змінюється (логін/логаут), онови ViewModels:

```python
def _on_user_changed(self, user):
    """Handle user change — recreate ViewModels."""
    self._current_user = user
    
    # Recreate ViewModels with new user
    if hasattr(self, '_monitoring_service'):
        self._dashboard_vm = DashboardViewModel(
            current_user=user,
            monitoring_service=self._monitoring_service,
            analysis_service=self._analysis_service,
        )
        self._measurements_vm = MeasurementsViewModel(
            current_user=user,
            monitoring_service=self._monitoring_service,
        )
    
    # Update pages
    if hasattr(self, '_dashboard_page'):
        self._dashboard_page.deleteLater()
    if hasattr(self, '_measurements_page'):
        self._measurements_page.deleteLater()
    
    self._dashboard_page = DashboardPageRefactored(self._dashboard_vm)
    self._measurements_page = MeasurementsPageRefactored(self._measurements_vm)
    
    # Refresh pages stack
    self._refresh_pages()
```

### 5. Очищення ресурсів

Додай очищення при закритті:

```python
def closeEvent(self, event):
    """Cleanup on close."""
    if hasattr(self, '_db'):
        self._db.close()
    event.accept()
```

## Переваги нової архітектури

### Стара архітектура:
```
UI Page → Database (прямий запит)
```

### Нова архітектура (MVVM):
```
UI Page → ViewModel → Service → Repository → Database
                      ↓
                   DTOs
```

**Переваги:**
1. ✅ **Тестованість** — ViewModels можна тестувати окремо від UI
2. ✅ **Чистота** — UI не знає про базу даних
3. ✅ **Повторне використання** — той самий ViewModel для різних Views
4. ✅ **Типізація** — DTOs замість словників
5. ✅ **Сигнали** — автоматичне оновлення UI при зміні даних

## Як тестувати

```python
# Тест ViewModel без UI
from app.presentation.view_models import DashboardViewModel

vm = DashboardViewModel(user, monitoring_service, analysis_service)
vm.load()

assert vm.latest_measurement is not None
assert vm.daily_stats["total_measurements"] > 0
```

## Повна інтеграція vs Часткова

### Часткова (рекомендовано зараз):
- Залишити старі pages як fallback
- Використовувати нові `*Refactored` pages
- Можна перемикатися через конфігурацію

### Повна (після тестування):
- Видалити старі файли
- Перейменувати `*Refactored` → звичайні імена
- Оновити всі imports

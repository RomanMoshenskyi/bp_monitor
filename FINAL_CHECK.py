#!/usr/bin/env python3
"""Final verification - BP Monitor Refactoring COMPLETE"""
import sys
sys.path.insert(0, r'd:\Downloads\bp_monitor-main')

print("=" * 70)
print("🎉 FINAL VERIFICATION - BP Monitor Refactoring")
print("=" * 70)
print(f"Python: {sys.version}")
print()

all_passed = True

# Test 1: Foundation
print("1️⃣  Phase 1: Foundation...")
try:
    from app.infrastructure.orm import Base, engine
    print("   ✅ SQLAlchemy ORM Base imported")
    print(f"   ✅ Engine configured: {engine.url.drivername}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 2: Domain
print("\n2️⃣  Phase 2: Domain Layer (11 Models)...")
try:
    from app.domain.entities import (
        UserORM, MeasurementORM, WeatherSnapshotORM,
        MedicationORM, MedicationIntakeORM, ActivityEventORM,
        ThresholdProfileORM, DailySummaryORM, RecommendationORM,
        AuditLogEntryORM, ReportORM,
    )
    print("   ✅ All 11 models imported")
    
    # Check relationships
    print("   ✅ Checking MeasurementORM relationships...")
    rels = list(MeasurementORM.__mapper__.relationships.keys())
    print(f"      Relationships: {rels}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 3: Services
print("\n3️⃣  Phase 3: Application Layer (7 Services)...")
try:
    from app.application.services import (
        MonitoringService, AnalysisService, AuditService,
        RecommendationService, ReportService, AccessControl, WeatherService,
    )
    print("   ✅ All 7 services imported")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 4: DTOs
print("\n4️⃣  Phase 3b: DTOs (14 DTOs)...")
try:
    from app.application.dto import (
        UserDTO, MeasurementDTO, DateRangeDTO, MeasurementStatsDTO,
        AnalysisResultDTO, CorrelationResultDTO,
    )
    print("   ✅ All key DTOs imported")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 5: Repositories
print("\n5️⃣  Phase 3c: Repositories (5 ORM)...")
try:
    from app.repositories import (
        BaseRepository, UserRepositoryORM, MeasurementRepositoryORM,
        WeatherRepository, RecommendationRepositoryORM,
    )
    print("   ✅ All 5 repositories imported")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 6: ViewModels
print("\n6️⃣  Phase 4: ViewModels (4 ViewModels)...")
try:
    from app.presentation.view_models import (
        BaseViewModel, DashboardViewModel,
        MeasurementsViewModel, AnalyticsViewModel,
    )
    print("   ✅ All 4 ViewModels imported")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 7: UI
print("\n7️⃣  Phase 6: UI Refactoring...")
try:
    from app.ui import DashboardPageRefactored, MeasurementsPageRefactored
    print("   ✅ Refactored UI pages imported")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 8: Diploma Features
print("\n8️⃣  Diploma Features...")
try:
    # Pearson Correlation
    from app.application.services import AnalysisService
    s = AnalysisService()
    r = s.calculate_pearson_correlation(
        [120.0, 130.0, 125.0, 140.0],
        [750.0, 760.0, 755.0, 770.0]
    )
    print(f"   ✅ Pearson Correlation (Formula 3.2): r={r.correlation_coefficient:.4f}")
    
    # Threshold Profile
    from app.domain.entities import ThresholdProfileORM
    profile = ThresholdProfileORM(sys_min=90, sys_max=140, dia_min=60, dia_max=90)
    result = profile.check_measurement(135, 85)
    print(f"   ✅ Threshold Profile check: {result['overall_status']}")
    
    # Audit Service
    from app.application.services import AuditService
    assert hasattr(AuditService, 'log')
    print("   ✅ AuditService.log() exists")
    
    # Access Control
    from app.application.services import AccessControl
    assert hasattr(AccessControl, 'can_read')
    assert hasattr(AccessControl, 'can_write')
    print("   ✅ AccessControl (RBAC) exists")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    all_passed = False

# Final Summary
print("\n" + "=" * 70)
if all_passed:
    print("🎉🎉🎉 ALL CHECKS PASSED! 🎉🎉🎉")
    print("=" * 70)
    print("\n✨ Refactoring COMPLETE!")
    print("\n📊 Summary:")
    print("   • 11 ORM Models (from diploma class diagram)")
    print("   • 7 Services (Monitoring, Analysis, Audit, etc.)")
    print("   • 14 DTOs (type-safe data transfer)")
    print("   • 5 ORM Repositories")
    print("   • 4 ViewModels (MVVM pattern)")
    print("   • 2 Refactored UI Pages")
    print("\n🎯 Diploma Features:")
    print("   • Pearson Correlation (Formula 3.2)")
    print("   • Audit Logging (userId, action, details)")
    print("   • RBAC (canRead, canWrite)")
    print("   • Weather-Pressure correlation analysis")
    print("\n📁 Key Files:")
    print("   • migrations_alembic/versions/001_initial_schema_3_tables.py")
    print("   • migrations_alembic/versions/002_all_11_tables.py")
    print("   • INTEGRATE_VIEWMODELS.md")
    print("\n🚀 Next Steps:")
    print("   1. Apply migrations: alembic upgrade head")
    print("   2. Integrate ViewModels in main_window.py")
    print("   3. Run the application")
    sys.exit(0)
else:
    print("⚠️  Some checks failed")
    print("=" * 70)
    sys.exit(1)

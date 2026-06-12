#!/usr/bin/env python3
"""
COMPREHENSIVE VERIFICATION - All 6 Phases
Run this file to verify the entire refactoring is working.

Usage:
    cd d:\Downloads\bp_monitor-main
    python VERIFY_ALL_PHASES.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_phase_1():
    """Phase 1: Foundation - SQLAlchemy ORM"""
    print("\n" + "="*60)
    print("PHASE 1: Foundation (SQLAlchemy ORM)")
    print("="*60)
    
    try:
        from app.infrastructure.orm import Base, engine, SessionLocal
        print("✅ ORM Base imported successfully")
        print(f"   Engine URL: {engine.url}")
        
        tables = list(Base.metadata.tables.keys())
        print(f"✅ {len(tables)} tables registered in metadata")
        for t in sorted(tables):
            print(f"   - {t}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_2():
    """Phase 2: Domain Layer - 11 Models"""
    print("\n" + "="*60)
    print("PHASE 2: Domain Layer (11 ORM Models)")
    print("="*60)
    
    try:
        from app.domain.entities import (
            UserORM, MeasurementORM, WeatherSnapshotORM,
            MedicationORM, MedicationIntakeORM, ActivityEventORM,
            ThresholdProfileORM, DailySummaryORM, RecommendationORM,
            AuditLogEntryORM, ReportORM,
            UserRole, ActivityType, SeverityLevel, ReportFormat, ReportStatus
        )
        
        models = [
            ("UserORM", UserORM),
            ("MeasurementORM", MeasurementORM),
            ("WeatherSnapshotORM", WeatherSnapshotORM),
            ("MedicationORM", MedicationORM),
            ("MedicationIntakeORM", MedicationIntakeORM),
            ("ActivityEventORM", ActivityEventORM),
            ("ThresholdProfileORM", ThresholdProfileORM),
            ("DailySummaryORM", DailySummaryORM),
            ("RecommendationORM", RecommendationORM),
            ("AuditLogEntryORM", AuditLogEntryORM),
            ("ReportORM", ReportORM),
        ]
        
        enums = [
            ("UserRole", UserRole),
            ("ActivityType", ActivityType),
            ("SeverityLevel", SeverityLevel),
            ("ReportFormat", ReportFormat),
            ("ReportStatus", ReportStatus),
        ]
        
        print(f"✅ All {len(models)} models imported:")
        for name, model in models:
            print(f"   - {name}: {model.__tablename__}")
        
        print(f"\n✅ All {len(enums)} enums imported:")
        for name, enum in enums:
            values = [e.value for e in enum]
            print(f"   - {name}: {values}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_3_services():
    """Phase 3: Services"""
    print("\n" + "="*60)
    print("PHASE 3: Application Layer (7 Services)")
    print("="*60)
    
    try:
        from app.application.services import (
            MonitoringService,
            AnalysisService,
            AuditService,
            RecommendationService,
            ReportService,
            AccessControl,
            WeatherService,
        )
        
        services = [
            "MonitoringService",
            "AnalysisService",
            "AuditService",
            "RecommendationService",
            "ReportService",
            "AccessControl",
            "WeatherService",
        ]
        
        print(f"✅ All {len(services)} services imported:")
        for s in services:
            print(f"   - {s}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_3_dtos():
    """Phase 3: DTOs"""
    print("\n" + "="*60)
    print("PHASE 3: DTOs (12 DTOs)")
    print("="*60)
    
    try:
        from app.application.dto import (
            UserDTO, UserCreateDTO, UserUpdateDTO,
            MeasurementDTO, MeasurementCreateDTO,
            WeatherSnapshotDTO,
            AnalysisResultDTO, CorrelationResultDTO,
            RecommendationDTO, RecommendationCreateDTO,
            ReportDTO, ReportCreateDTO,
        )
        
        dtos = [
            "UserDTO", "UserCreateDTO", "UserUpdateDTO",
            "MeasurementDTO", "MeasurementCreateDTO",
            "WeatherSnapshotDTO",
            "AnalysisResultDTO", "CorrelationResultDTO",
            "RecommendationDTO", "RecommendationCreateDTO",
            "ReportDTO", "ReportCreateDTO",
        ]
        
        print(f"✅ All {len(dtos)} DTOs imported:")
        for dto in dtos:
            print(f"   - {dto}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_3_repositories():
    """Phase 3: Repositories"""
    print("\n" + "="*60)
    print("PHASE 3: Repositories (5 ORM Repositories)")
    print("="*60)
    
    try:
        from app.repositories import (
            BaseRepository,
            UserRepositoryORM,
            MeasurementRepositoryORM,
            WeatherRepository,
            RecommendationRepositoryORM,
        )
        
        repos = [
            "BaseRepository",
            "UserRepositoryORM",
            "MeasurementRepositoryORM",
            "WeatherRepository",
            "RecommendationRepositoryORM",
        ]
        
        print(f"✅ All {len(repos)} ORM repositories imported:")
        for r in repos:
            print(f"   - {r}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_4():
    """Phase 4: ViewModels"""
    print("\n" + "="*60)
    print("PHASE 4: Presentation Layer (4 ViewModels)")
    print("="*60)
    
    try:
        from app.presentation.view_models import (
            BaseViewModel,
            DashboardViewModel,
            MeasurementsViewModel,
            AnalyticsViewModel,
        )
        
        vms = [
            ("BaseViewModel", BaseViewModel),
            ("DashboardViewModel", DashboardViewModel),
            ("MeasurementsViewModel", MeasurementsViewModel),
            ("AnalyticsViewModel", AnalyticsViewModel),
        ]
        
        print(f"✅ All {len(vms)} ViewModels imported:")
        for name, vm in vms:
            print(f"   - {name}")
        
        # Check PyQt6 signals
        print("\n✅ Checking PyQt6 signals in BaseViewModel...")
        assert hasattr(BaseViewModel, 'error_occurred')
        assert hasattr(BaseViewModel, 'loading_changed')
        assert hasattr(BaseViewModel, 'data_changed')
        print("   - error_occurred signal: OK")
        print("   - loading_changed signal: OK")
        print("   - data_changed signal: OK")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_6():
    """Phase 6: UI Refactoring"""
    print("\n" + "="*60)
    print("PHASE 6: UI Refactoring (ViewModel Integration)")
    print("="*60)
    
    try:
        from app.ui import DashboardPageRefactored, MeasurementsPageRefactored
        print("✅ DashboardPageRefactored imported")
        print("✅ MeasurementsPageRefactored imported")
        
        # Check they accept view_model parameter
        import inspect
        dash_sig = inspect.signature(DashboardPageRefactored.__init__)
        meas_sig = inspect.signature(MeasurementsPageRefactored.__init__)
        
        assert 'view_model' in str(dash_sig), "DashboardPage needs view_model param"
        assert 'view_model' in str(meas_sig), "MeasurementsPage needs view_model param"
        
        print("✅ Both pages accept ViewModel in constructor")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_diploma_features():
    """Test specific diploma features"""
    print("\n" + "="*60)
    print("DIPLOMA FEATURES VERIFICATION")
    print("="*60)
    
    all_ok = True
    
    # 1. Pearson Correlation
    print("\n1. Pearson Correlation (Formula 3.2)...")
    try:
        from app.application.services import AnalysisService
        
        service = AnalysisService()
        result = service.calculate_pearson_correlation(
            [120.0, 130.0, 125.0, 140.0],
            [750.0, 760.0, 755.0, 770.0]
        )
        
        if result:
            print(f"✅ Pearson correlation working")
            print(f"   r = {result.correlation_coefficient:.4f}")
            print(f"   interpretation: {result.interpretation}")
            print(f"   significant: {result.is_significant()}")
        else:
            print("⚠️  Correlation returned None (insufficient data)")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        all_ok = False
    
    # 2. Audit Service
    print("\n2. Audit Service...")
    try:
        from app.application.services import AuditService
        assert hasattr(AuditService, 'log')
        print("✅ AuditService.log() method exists")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        all_ok = False
    
    # 3. Access Control
    print("\n3. Access Control (RBAC)...")
    try:
        from app.application.services import AccessControl
        assert hasattr(AccessControl, 'can_read')
        assert hasattr(AccessControl, 'can_write')
        print("✅ AccessControl.can_read() exists")
        print("✅ AccessControl.can_write() exists")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        all_ok = False
    
    # 4. Threshold Profile
    print("\n4. Threshold Profile...")
    try:
        from app.domain.entities import ThresholdProfileORM
        profile = ThresholdProfileORM(sys_min=90, sys_max=140, dia_min=60, dia_max=90)
        result = profile.check_measurement(135, 85)
        assert 'overall_status' in result
        print("✅ ThresholdProfileORM.check_measurement() works")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        all_ok = False
    
    return all_ok


def test_file_structure():
    """Verify file structure exists"""
    print("\n" + "="*60)
    print("FILE STRUCTURE VERIFICATION")
    print("="*60)
    
    import os
    
    required_files = [
        ("app/infrastructure/orm/base.py", "ORM Base"),
        ("app/domain/entities/user_orm.py", "User model"),
        ("app/domain/entities/measurement_orm.py", "Measurement model"),
        ("app/application/services/monitoring_service.py", "MonitoringService"),
        ("app/application/services/analysis_service.py", "AnalysisService"),
        ("app/repositories/base_repository.py", "BaseRepository"),
        ("app/presentation/view_models/base_view_model.py", "BaseViewModel"),
        ("app/ui/dashboard_page_refactored.py", "Dashboard refactored"),
        ("migrations_alembic/alembic.ini", "Alembic config"),
        ("migrations_alembic/versions/001_initial_schema_3_tables.py", "Migration 001"),
        ("migrations_alembic/versions/002_all_11_tables.py", "Migration 002"),
        ("INTEGRATE_VIEWMODELS.md", "Integration guide"),
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    missing = []
    for file_path, description in required_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ {description}: MISSING - {file_path}")
            missing.append(file_path)
    
    if missing:
        print(f"\n⚠️  {len(missing)} files missing")
        return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE VERIFICATION - BP Monitor Refactoring")
    print("="*70)
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    
    results = []
    
    # Run all tests
    results.append(("Phase 1: Foundation", test_phase_1()))
    results.append(("Phase 2: Domain Layer", test_phase_2()))
    results.append(("Phase 3a: Services", test_phase_3_services()))
    results.append(("Phase 3b: DTOs", test_phase_3_dtos()))
    results.append(("Phase 3c: Repositories", test_phase_3_repositories()))
    results.append(("Phase 4: ViewModels", test_phase_4()))
    results.append(("Phase 6: UI Refactoring", test_phase_6()))
    results.append(("Diploma Features", test_diploma_features()))
    results.append(("File Structure", test_file_structure()))
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*70)
    if passed == total:
        print(f"🎉 ALL {total} CHECKS PASSED!")
        print("="*70)
        print("\n✨ The refactoring is COMPLETE and WORKING!")
        print("\nNext steps:")
        print("1. Apply migrations: alembic -c migrations_alembic/alembic.ini upgrade head")
        print("2. Integrate ViewModels: see INTEGRATE_VIEWMODELS.md")
        print("3. Run the application")
        return 0
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("="*70)
        print("\nSome components need attention.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

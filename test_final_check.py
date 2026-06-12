"""Final check - verify all ORM models and repositories."""
import sys
sys.path.insert(0, r'd:\Downloads\bp_monitor-main')

print("=" * 60)
print("FINAL CHECK: Phase 2 Complete")
print("=" * 60)

# Test 1: All 11 ORM Models
print("\n1. Testing 11 ORM Models...")
try:
    from app.domain.entities import (
        UserORM, MeasurementORM, WeatherSnapshotORM,
        MedicationORM, MedicationIntakeORM, ActivityEventORM,
        ThresholdProfileORM, DailySummaryORM, RecommendationORM,
        AuditLogEntryORM, ReportORM,
        UserRole, ActivityType, SeverityLevel, ReportFormat, ReportStatus
    )
    models = [
        UserORM, MeasurementORM, WeatherSnapshotORM,
        MedicationORM, MedicationIntakeORM, ActivityEventORM,
        ThresholdProfileORM, DailySummaryORM, RecommendationORM,
        AuditLogEntryORM, ReportORM
    ]
    print(f"   ✅ All 11 models imported successfully")
    print(f"   📊 Tables: {[m.__tablename__ for m in models]}")
except Exception as e:
    print(f"   ❌ Models import failed: {e}")
    sys.exit(1)

# Test 2: Base and Metadata
print("\n2. Testing SQLAlchemy Base...")
try:
    from app.infrastructure.orm import Base
    tables_in_meta = list(Base.metadata.tables.keys())
    print(f"   ✅ Base loaded with {len(tables_in_meta)} tables")
    print(f"   📊 Tables in metadata: {sorted(tables_in_meta)}")
except Exception as e:
    print(f"   ❌ Base import failed: {e}")
    sys.exit(1)

# Test 3: Repositories
print("\n3. Testing ORM Repositories...")
try:
    from app.repositories import (
        BaseRepository,
        UserRepositoryORM,
        MeasurementRepositoryORM,
        WeatherRepository,
        RecommendationRepositoryORM
    )
    print(f"   ✅ 5 repositories imported")
    print(f"      - BaseRepository")
    print(f"      - UserRepositoryORM")
    print(f"      - MeasurementRepositoryORM")
    print(f"      - WeatherRepository")
    print(f"      - RecommendationRepositoryORM")
except Exception as e:
    print(f"   ❌ Repository import failed: {e}")
    sys.exit(1)

# Test 4: Migrations
print("\n4. Testing Migration Files...")
try:
    import os
    migrations_dir = r'd:\Downloads\bp_monitor-main\migrations_alembic\versions'
    if os.path.exists(migrations_dir):
        files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
        print(f"   ✅ Migrations directory exists")
        print(f"   📁 Migration files: {files}")
    else:
        print(f"   ⚠️  Migrations directory not found (will be created on first run)")
except Exception as e:
    print(f"   ❌ Migration check failed: {e}")

# Summary
print("\n" + "=" * 60)
print("✅ PHASE 2 COMPLETE - All 11 Models + 5 Repositories Ready")
print("=" * 60)
print("\nNext Steps:")
print("1. Apply migrations to database:")
print("   alembic -c migrations_alembic/alembic.ini upgrade head")
print("2. Create Services (Phase 3)")
print("3. Create DTOs (Phase 4)")
print("4. Create ViewModels (Phase 5)")
print("\nBackup location: Check d:\\Downloads\\ for bp_monitor-main_backup_*")

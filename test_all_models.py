"""Test all 11 ORM models can be imported."""
import sys
sys.path.insert(0, r'd:\Downloads\bp_monitor-main')

print("Testing all 11 ORM model imports...")

try:
    from app.domain.entities import (
        # 11 models
        UserORM,
        MeasurementORM,
        WeatherSnapshotORM,
        MedicationORM,
        MedicationIntakeORM,
        ActivityEventORM,
        ThresholdProfileORM,
        DailySummaryORM,
        RecommendationORM,
        AuditLogEntryORM,
        ReportORM,
        # Enums
        UserRole,
        ActivityType,
        SeverityLevel,
        ReportFormat,
        ReportStatus,
    )
    
    from app.infrastructure.orm import Base
    
    print("✅ All imports successful")
    
    # Verify table names
    tables = [
        UserORM.__tablename__,
        MeasurementORM.__tablename__,
        WeatherSnapshotORM.__tablename__,
        MedicationORM.__tablename__,
        MedicationIntakeORM.__tablename__,
        ActivityEventORM.__tablename__,
        ThresholdProfileORM.__tablename__,
        DailySummaryORM.__tablename__,
        RecommendationORM.__tablename__,
        AuditLogEntryORM.__tablename__,
        ReportORM.__tablename__,
    ]
    
    print(f"\n📊 Tables ({len(tables)}):")
    for t in tables:
        print(f"  - {t}")
    
    # Verify in metadata
    metadata_tables = list(Base.metadata.tables.keys())
    print(f"\n📊 Tables in Base.metadata ({len(metadata_tables)}):")
    for t in sorted(metadata_tables):
        print(f"  - {t}")
    
    print("\n🎉 All 11 ORM models loaded successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

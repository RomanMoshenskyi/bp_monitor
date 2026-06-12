"""Quick test to verify ORM imports work."""
import sys
sys.path.insert(0, r'd:\Downloads\bp_monitor-main')

print("Testing ORM imports...")

try:
    from app.infrastructure.orm import Base, engine
    print(f"✅ Base imported, engine: {engine.url}")
    
    from app.domain.entities import UserORM, MeasurementORM, WeatherSnapshotORM, UserRole
    print(f"✅ UserORM: {UserORM.__tablename__}")
    print(f"✅ MeasurementORM: {MeasurementORM.__tablename__}")
    print(f"✅ WeatherSnapshotORM: {WeatherSnapshotORM.__tablename__}")
    print(f"✅ UserRole: {list(UserRole)}")
    
    tables = list(Base.metadata.tables.keys())
    print(f"✅ Tables registered: {tables}")
    
    print("\n🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

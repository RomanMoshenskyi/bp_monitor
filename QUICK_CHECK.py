#!/usr/bin/env python3
"""Quick check after fixes"""
import sys
sys.path.insert(0, r'd:\Downloads\bp_monitor-main')

print("Checking fixes...")

# 1. Check DTOs
try:
    from app.application.dto import MeasurementStatsDTO, DateRangeDTO
    print("✅ MeasurementStatsDTO imported")
    print("✅ DateRangeDTO imported")
except Exception as e:
    print(f"❌ DTOs: {e}")

# 2. Check UserORM relationships
try:
    from app.domain.entities import UserORM
    print(f"✅ UserORM relationships: {list(UserORM.__mapper__.relationships.keys())}")
except Exception as e:
    print(f"❌ UserORM: {e}")

# 3. Check UI imports
try:
    from app.ui import DashboardPageRefactored, MeasurementsPageRefactored
    print("✅ DashboardPageRefactored imported")
    print("✅ MeasurementsPageRefactored imported")
except Exception as e:
    print(f"❌ UI: {e}")

# 4. Check tables
try:
    from app.domain.entities import *
    from app.infrastructure.orm import Base
    tables = list(Base.metadata.tables.keys())
    print(f"✅ Tables in metadata: {len(tables)}")
    for t in sorted(tables):
        print(f"   - {t}")
except Exception as e:
    print(f"❌ Tables: {e}")

print("\nDone!")

#!/usr/bin/env python3
"""Apply migrations using SQLAlchemy (bypasses encoding issues)."""
import sys
sys.path.insert(0, r'd:\Downloads\bp_monitor-main')

from app.infrastructure.orm import engine, Base
from app.domain.entities import *  # Import all models

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully!")

# Verify
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\n📊 Created {len(tables)} tables:")
for t in sorted(tables):
    print(f"   - {t}")

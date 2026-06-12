#!/usr/bin/env python3
"""Test database connection with debug output"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set DB config
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "bp_monitor"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "postgres"

print("Testing database connection...")
print(f"Python version: {sys.version}")

try:
    from app.infrastructure.orm import get_database_url
    url = get_database_url()
    print(f"Database URL: {url}")
    
    # Try to connect
    from app.infrastructure.orm import engine
    from sqlalchemy import text
    
    print("Connecting to database...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"✅ Connection successful! Result: {result.scalar()}")
    
    # Create tables
    print("Creating tables...")
    from app.infrastructure.orm import Base
    from app.domain.entities import UserORM  # Import at least one model
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created!")
    
    # List tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📊 Tables: {tables}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

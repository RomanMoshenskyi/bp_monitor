#!/usr/bin/env python3
"""
Script to apply new database schema for extended functionality.
Creates tables for doctor reports, prescriptions, and medication intakes.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect, init_schema
from app.logging_config import get_logger

_logger = get_logger(__name__)


def apply_new_tables():
    """Apply new tables schema."""
    _logger.info("Applying new database schema...")
    
    schema_path = Path(__file__).parent / "schema_new_tables.sql"
    
    if not schema_path.exists():
        _logger.error(f"Schema file not found: {schema_path}")
        return False
    
    sql = schema_path.read_text(encoding="utf-8")
    
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        _logger.info("New tables created successfully!")
        
        # Verify tables were created
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            _logger.info(f"Tables in database ({len(tables)}): {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        _logger.error(f"Failed to apply schema: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main entry point."""
    print("=" * 60)
    print("🔧 Applying new database schema")
    print("=" * 60)
    
    # First ensure base schema is initialized
    print("\n📋 Initializing base schema...")
    init_schema()
    
    # Apply new tables
    print("\n📋 Creating new tables...")
    if apply_new_tables():
        print("\n✅ Success! New tables created.")
        print("\nYou can now use the new features:")
        print("  - Doctor medical reports")
        print("  - Prescription management")
        print("  - Medication intake tracking")
        return 0
    else:
        print("\n❌ Failed to create new tables.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

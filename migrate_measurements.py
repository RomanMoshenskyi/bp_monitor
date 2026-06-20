#!/usr/bin/env python3
"""Migration to rename timestamp to measured_at in measurements table."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect

def migrate():
    conn = connect()
    try:
        cur = conn.cursor()
        
        # Check if timestamp column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'measurements' AND column_name = 'timestamp'
        """)
        has_timestamp = cur.fetchone() is not None
        
        if has_timestamp:
            print("Found 'timestamp' column, renaming to 'measured_at'...")
            cur.execute("ALTER TABLE measurements RENAME COLUMN timestamp TO measured_at")
            print("✅ Renamed timestamp → measured_at")
        else:
            print("No 'timestamp' column found (may already be migrated)")
        
        # Check if we need to add user_id foreign key and other columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'measurements' AND column_name = 'user_id'
        """)
        has_user_id = cur.fetchone() is not None
        
        if not has_user_id:
            print("Adding user_id column...")
            cur.execute("ALTER TABLE measurements ADD COLUMN user_id INTEGER")
            print("✅ Added user_id column")
        
        # Add weather_snapshot_id if missing
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'measurements' AND column_name = 'weather_snapshot_id'
        """)
        has_weather = cur.fetchone() is not None
        
        if not has_weather:
            print("Adding weather_snapshot_id column...")
            cur.execute("ALTER TABLE measurements ADD COLUMN weather_snapshot_id INTEGER")
            print("✅ Added weather_snapshot_id column")
        
        # Add latitude if missing
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'measurements' AND column_name = 'latitude'
        """)
        has_latitude = cur.fetchone() is not None
        
        if not has_latitude:
            print("Adding latitude column...")
            cur.execute("ALTER TABLE measurements ADD COLUMN latitude FLOAT")
            print("✅ Added latitude column")
        
        # Add longitude if missing
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'measurements' AND column_name = 'longitude'
        """)
        has_longitude = cur.fetchone() is not None
        
        if not has_longitude:
            print("Adding longitude column...")
            cur.execute("ALTER TABLE measurements ADD COLUMN longitude FLOAT")
            print("✅ Added longitude column")
        
        # Add updated_at if missing
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'measurements' AND column_name = 'updated_at'
        """)
        has_updated_at = cur.fetchone() is not None
        
        if not has_updated_at:
            print("Adding updated_at column...")
            cur.execute("ALTER TABLE measurements ADD COLUMN updated_at TIMESTAMP")
            print("✅ Added updated_at column")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify final schema
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'measurements'
            ORDER BY ordinal_position
        """)
        print("\nFinal columns in measurements table:")
        for row in cur.fetchall():
            print(f"  - {row[0]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

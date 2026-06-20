#!/usr/bin/env python3
"""Create audit_logs table."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect

def main():
    conn = connect()
    cur = conn.cursor()
    
    print("Creating audit_logs table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50),
            entity_id INTEGER,
            details TEXT,
            ip_address VARCHAR(45),
            user_agent VARCHAR(255),
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("Creating indexes...")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_id ON audit_logs(id)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON audit_logs(timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_user_action ON audit_logs(user_id, action)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_user_timestamp ON audit_logs(user_id, timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_action_timestamp ON audit_logs(action, timestamp)")
    
    conn.commit()
    print("✅ audit_logs table created successfully!")
    conn.close()

if __name__ == "__main__":
    main()

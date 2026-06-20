#!/usr/bin/env python3
"""
Run BP Monitor Application with proper setup
"""
import os
import sys
import subprocess

# Add project to path before any imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _patch_psycopg2_encoding():
    """Wrap psycopg2._connect to handle CP1251-encoded PostgreSQL error messages on Windows."""
    try:
        import psycopg2
        from psycopg2 import OperationalError

        _orig = psycopg2._connect

        def _safe_connect(dsn, connection_factory=None, **kwasync):
            try:
                return _orig(dsn, connection_factory=connection_factory, **kwasync)
            except UnicodeDecodeError as e:
                raw = getattr(e, 'object', b'')
                try:
                    msg = raw.decode('cp1251', errors='replace')
                except Exception:
                    msg = raw.decode('latin-1', errors='replace')
                raise OperationalError(msg) from None

        psycopg2._connect = _safe_connect
    except ImportError:
        pass


def _create_database_if_not_exists(host, port, user, password, dbname):
    """Connect to the postgres system DB and create dbname if it does not exist."""
    import psycopg2
    from psycopg2 import OperationalError
    try:
        conn = psycopg2.connect(
            host=host, port=int(port),
            dbname='postgres', user=user, password=password,
            connect_timeout=5,
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cur.fetchone():
                print(f"   ✅ Database '{dbname}' already exists.")
            else:
                cur.execute(f'CREATE DATABASE "{dbname}"')
                print(f"   ✅ Database '{dbname}' created successfully!")
        conn.close()
        return True
    except OperationalError as e:
        print(f"   ❌ Cannot reach PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Failed to create database: {e}")
        return False


def setup_database():
    """Apply schema_final.sql — single idempotent canonical schema."""
    print("\n🔧 Applying database schema...")

    try:
        import psycopg2
        from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_final.sql")
        sql = open(schema_path, encoding="utf-8").read()

        conn = psycopg2.connect(
            host=DB_HOST, port=int(DB_PORT), dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
            connect_timeout=5, options="-c client_encoding=UTF8",
        )
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        conn.close()
        print("   ✅ Schema applied!")

        # Seed default users if users table is empty
        _seed_users(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)

        # Report existing tables
        conn = psycopg2.connect(
            host=DB_HOST, port=int(DB_PORT), dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
        )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
            tables = [row[0] for row in cur.fetchall()]
        conn.close()
        print(f"\n   📊 Tables in database ({len(tables)}):")
        for t in tables:
            print(f"      - {t}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"   ❌ Schema setup failed: {e}")
        print("\n   💡 Make sure PostgreSQL is running and accessible")
        return False

    return True


def _seed_users(host, port, dbname, user, password):
    """Insert default admin/doctor/patient accounts if the users table is empty."""
    import psycopg2
    import hashlib, secrets

    def _hash(pw):
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000)
        return f"{salt}${digest.hex()}"

    defaults = [
        ("admin",   "AdminPass123",   "Адміністратор",   "admin",   None),
        ("doctor",  "DoctorPass123",  "Лікар Іваненко",  "doctor",  None),
        ("patient", "PatientPass123", "Пацієнт Демо",    "patient", 30),
    ]

    conn = psycopg2.connect(
        host=host, port=int(port), dbname=dbname, user=user, password=password,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            if cur.fetchone()[0] > 0:
                return  # already seeded
            for username, pw, full_name, role, age in defaults:
                cur.execute(
                    "INSERT INTO users (username, password_hash, full_name, role, age) "
                    "VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (username, _hash(pw), full_name, role, age),
                )
        conn.commit()
        print("   ✅ Default users seeded (admin / doctor / patient)")
    finally:
        conn.close()

def main():
    print("=" * 80)
    print("🚀 BP Monitor - Setup & Run")
    print("=" * 80)
    
    # Database configuration
    db_config = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "bp_monitor",
        "DB_USER": "postgres",
        "DB_PASSWORD": "1234"
    }
    
    print("\n📋 Database Configuration:")
    for key, value in db_config.items():
        display = value if "PASSWORD" not in key else "***"
        print(f"   {key}: {display}")
    
    # Set environment variables
    print("\n🔧 Setting environment variables...")
    for key, value in db_config.items():
        os.environ[key] = value
    
    # Patch psycopg2 so Cyrillic PostgreSQL messages don't cause UnicodeDecodeError
    _patch_psycopg2_encoding()

    # Create the database if it does not exist yet
    print("\n🗄️  Checking / creating database...")
    if not _create_database_if_not_exists(
        db_config["DB_HOST"], db_config["DB_PORT"],
        db_config["DB_USER"], db_config["DB_PASSWORD"],
        db_config["DB_NAME"],
    ):
        return 1

    # Setup database
    if not setup_database():
        return 1
    
    # Run the application
    print("\n" + "=" * 80)
    print("🖥️  Starting BP Monitor Application...")
    print("=" * 80)
    
    try:
        # Clear Python cache to ensure fresh imports
        import shutil
        for root, dirs, files in os.walk("."):
            for d in dirs:
                if d == "__pycache__":
                    try:
                        shutil.rmtree(os.path.join(root, d))
                    except:
                        pass
        
        # Run the app
        subprocess.run([sys.executable, "main.py"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Application exited with error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

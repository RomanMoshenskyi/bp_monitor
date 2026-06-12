#!/usr/bin/env python3
"""Test direct psycopg2 connection"""
import os
import sys

# Fix encoding for Windows
import locale
if sys.platform == 'win32':
    # Set UTF-8 encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    # Set locale
    try:
        locale.setlocale(locale.LC_ALL, 'uk_UA.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass

os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "bp_monitor"
os.environ["DB_USER"] = "postgres"
# Try empty password or simple password
os.environ["DB_PASSWORD"] = ""

print("Testing direct psycopg2 connection...")
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Default encoding: {sys.getdefaultencoding()}")

# Set Windows ANSI code page
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(1251)
    kernel32.SetConsoleOutputCP(1251)

try:
    import psycopg2
    
    # Use kwargs instead of connection string
    print("Connecting with kwargs...")
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="bp_monitor",
        user="postgres",
        password="postgres",
    )
    print("✅ Connected successfully!")
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print(f"✅ Query result: {result}")
    
    cursor.close()
    conn.close()
    print("✅ Connection closed")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

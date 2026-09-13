"""
KEFE PostgreSQL Setup Script
Run this once to create the kefe database and user.

Usage:
    python scripts/setup_db.py

Requirements:
    - PostgreSQL 18 running on localhost:5432
    - postgres superuser password: prompted or set POSTGRES_PASSWORD env var
"""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

postgres_password = os.environ.get("POSTGRES_PASSWORD", "1234")

print(f"Connecting to PostgreSQL as postgres...")
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password=postgres_password,
        dbname="postgres",
        connect_timeout=10,
    )
except psycopg2.OperationalError as e:
    print(f"ERROR: Could not connect: {e}")
    print("Make sure PostgreSQL is running and the password is correct.")
    print("Set POSTGRES_PASSWORD env var if your password is not '1234'.")
    sys.exit(1)

conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_user WHERE usename = 'kefe'")
if not cur.fetchone():
    cur.execute("CREATE USER kefe WITH PASSWORD 'kefe'")
    print("✓ User 'kefe' created")
else:
    print("✓ User 'kefe' already exists")

cur.execute("SELECT 1 FROM pg_database WHERE datname = 'kefe'")
if not cur.fetchone():
    cur.execute("CREATE DATABASE kefe OWNER kefe")
    print("✓ Database 'kefe' created")
else:
    print("✓ Database 'kefe' already exists")

cur.execute("GRANT ALL PRIVILEGES ON DATABASE kefe TO kefe")
print("✓ Privileges granted")

conn.close()

print()
print("Database setup complete!")
print()
print("Next steps:")
print("  1. cd services/api")
print("  2. python -m alembic upgrade head   (run migrations)")
print("  3. python scripts/seed_beta_catalog_postgres.py   (seed catalog)")
print("  4. scripts/start_api_postgres.bat   (start API)")
"""
KEFE Beta Catalog Seed Script
Seeds all 23 beta cases into PostgreSQL.

Usage:
    python scripts/seed_beta_catalog_postgres.py

Requirements:
    - PostgreSQL running, migrations applied (alembic upgrade head)
    - kefe database and user created (run setup_db.py first)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api', 'src'))

os.environ['KEFE_DATABASE_URL'] = 'postgresql+psycopg2://kefe:kefe@localhost:5432/kefe'
os.environ['KEFE_PERSISTENCE_BACKEND'] = 'postgres'

from kefe_api.infrastructure.seed_beta_catalog import seed_beta_catalog

print("Seeding beta catalog into PostgreSQL...")
seed_beta_catalog()
print("Done! 23 cases seeded.")
print()
print("Verify with:")
print("  curl http://localhost:8000/v1/cases?limit=30")
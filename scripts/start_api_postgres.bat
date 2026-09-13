@echo off
REM KEFE API — PostgreSQL mode
REM Run this script to start the API with persistent PostgreSQL storage.
REM Requirements: PostgreSQL 18 running on localhost:5432, database 'kefe', user 'kefe' password 'kefe'
REM 
REM First time setup:
REM   1. Run scripts\setup_db.py to create DB and user
REM   2. Run: cd services\api && python -m alembic upgrade head
REM   3. Run: python scripts\seed_beta_catalog_postgres.py

set KEFE_DATABASE_URL=postgresql+psycopg2://kefe:kefe@localhost:5432/kefe
set KEFE_PERSISTENCE_BACKEND=postgres
set KEFE_OTP_DELIVERY_MODE=CAPTURE
set KEFE_ENVIRONMENT=development

echo Starting KEFE API with PostgreSQL backend...
echo Database: %KEFE_DATABASE_URL%
echo.

cd /d %~dp0..\services\api\src
E:\Programs\Python\Python313\Scripts\uvicorn.exe kefe_api.main:app --host 0.0.0.0 --port 8000 --reload
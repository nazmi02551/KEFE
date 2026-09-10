# KEFE monorepo Makefile
# Covers: API, Admin Studio (Next.js), Flutter mobile, infrastructure, migrations, packages.
#
# Usage examples:
#   make api-test              — run API tests (in-memory backend)
#   make api-test-postgres     — run API tests against a live PostgreSQL instance
#   make admin-dev             — start Admin Studio dev server
#   make mobile-test           — run Flutter tests
#   make db-migrate            — apply pending migrations
#   make infra-up              — start full local stack (Postgres, Redis, MinIO)
#   make infra-down            — stop local stack
#   make check                 — run all linters and in-memory tests (CI-safe, no DB required)

.PHONY: \
  api-install api-lint api-format api-test api-test-postgres api-check api-dev \
  admin-install admin-dev admin-build admin-lint admin-check \
  mobile-test mobile-analyze mobile-build-android mobile-check \
  db-migrate db-migrate-down db-history db-current \
  infra-up infra-down infra-ps infra-logs \
  packages-validate \
  check check-all

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
API_DIR         := services/api
ADMIN_DIR       := apps/admin
MOBILE_DIR      := apps/mobile
INFRA_LOCAL     := infra/local

# ---------------------------------------------------------------------------
# API (FastAPI / Python)
# ---------------------------------------------------------------------------

api-install:
	cd $(API_DIR) && python -m pip install -e '.[dev]'

api-lint:
	cd $(API_DIR) && ruff check .

api-format:
	cd $(API_DIR) && ruff format .

api-test:
	cd $(API_DIR) && pytest --cov=kefe_api --cov-report=term-missing -p no:warnings

api-test-postgres:
	cd $(API_DIR) && KEFE_PERSISTENCE_BACKEND=postgres pytest --cov=kefe_api --cov-report=term-missing -p no:warnings

api-test-fast:
	cd $(API_DIR) && pytest -q -p no:warnings --ignore=tests/__pycache__

api-check: api-lint api-test

api-dev:
	cd $(API_DIR) && uvicorn kefe_api.main:app --reload --host 0.0.0.0 --port 8000

# ---------------------------------------------------------------------------
# Admin Studio (Next.js)
# ---------------------------------------------------------------------------

admin-install:
	cd $(ADMIN_DIR) && npm install

admin-dev:
	cd $(ADMIN_DIR) && npm run dev

admin-build:
	cd $(ADMIN_DIR) && npm run build

admin-lint:
	cd $(ADMIN_DIR) && npm run lint

admin-typecheck:
	cd $(ADMIN_DIR) && npm run typecheck

admin-check: admin-lint admin-typecheck

# ---------------------------------------------------------------------------
# Flutter Mobile
# ---------------------------------------------------------------------------

mobile-test:
	cd $(MOBILE_DIR) && flutter test

mobile-analyze:
	cd $(MOBILE_DIR) && flutter analyze

mobile-build-android:
	cd $(MOBILE_DIR) && flutter build apk --release

mobile-check: mobile-analyze mobile-test

# ---------------------------------------------------------------------------
# Database / Migrations (Alembic)
# ---------------------------------------------------------------------------

db-migrate:
	cd $(API_DIR) && alembic upgrade head

db-migrate-down:
	cd $(API_DIR) && alembic downgrade -1

db-history:
	cd $(API_DIR) && alembic history --verbose

db-current:
	cd $(API_DIR) && alembic current

db-generate:
	@echo "Usage: make db-generate MSG='short description'"
	cd $(API_DIR) && alembic revision --autogenerate -m "$(MSG)"

# ---------------------------------------------------------------------------
# Infrastructure (Docker Compose — local dev only)
# ---------------------------------------------------------------------------

infra-up:
	cd $(INFRA_LOCAL) && docker compose up -d

infra-down:
	cd $(INFRA_LOCAL) && docker compose down

infra-ps:
	cd $(INFRA_LOCAL) && docker compose ps

infra-logs:
	cd $(INFRA_LOCAL) && docker compose logs -f

infra-reset:
	cd $(INFRA_LOCAL) && docker compose down -v && docker compose up -d

# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

packages-validate:
	node packages/kefe-design-tokens/scripts/validate.mjs
	node packages/kefe-locale/scripts/validate.mjs
	node packages/kefe-test-fixtures/scripts/validate.mjs

web-test:
	cd apps/web && node tools/run_tests.mjs

web-dev:
	cd apps/web && npm run dev

web-build:
	cd apps/web && npm run build

# ---------------------------------------------------------------------------
# Aggregate targets
# ---------------------------------------------------------------------------

# CI-safe: runs without any Docker/DB dependency
check: api-lint api-test-fast admin-lint

# Full local check: requires infra-up first
check-all: api-check admin-check mobile-check packages-validate web-test
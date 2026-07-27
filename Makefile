.PHONY: api-install api-lint api-test api-check

api-install:
	cd services/api && python -m pip install -e '.[dev]'

api-lint:
	cd services/api && ruff check .

api-test:
	cd services/api && pytest --cov=kefe_api --cov-report=term-missing

api-check: api-lint api-test

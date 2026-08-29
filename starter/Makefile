SHELL := /bin/bash
PYTHON ?= python3

.PHONY: api-install api-test api-lint api-typecheck api-dev web-install web-check contracts-check ops-test check

api-install:
	cd services/api && uv pip install --python .venv/bin/python -e '.[dev]'

api-test:
	cd services/api && .venv/bin/pytest -q

api-lint:
	cd services/api && .venv/bin/ruff check src tests

api-typecheck:
	cd services/api && .venv/bin/mypy src

api-dev:
	cd services/api && .venv/bin/uvicorn citetrace_api.main:app --reload --host 0.0.0.0 --port 8000

web-install:
	corepack enable && pnpm --dir apps/web install

web-check:
	pnpm --dir apps/web typecheck && pnpm --dir apps/web build

contracts-check:
	cd .. && $(PYTHON) scripts/validate_package.py

ops-test:
	cd ops && ../services/api/.venv/bin/pytest tests -q

check: api-lint api-typecheck api-test ops-test contracts-check

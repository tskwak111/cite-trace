SHELL := /bin/bash
PYTHON ?= python3

.PHONY: api-install api-test api-lint api-typecheck api-dev web-install web-check contracts-check check

api-install:
	cd services/api && $(PYTHON) -m pip install -e '.[dev]'

api-test:
	cd services/api && pytest -q

api-lint:
	cd services/api && ruff check src tests

api-typecheck:
	cd services/api && mypy src

api-dev:
	cd services/api && uvicorn citetrace_api.main:app --reload --host 0.0.0.0 --port 8000

web-install:
	corepack enable && pnpm --dir apps/web install

web-check:
	pnpm --dir apps/web typecheck && pnpm --dir apps/web build

contracts-check:
	cd .. && $(PYTHON) scripts/validate_package.py

check: api-lint api-typecheck api-test contracts-check

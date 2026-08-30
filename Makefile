SHELL := /bin/bash
PYTHON ?= python3

# The release tool. Run `make release VERSION=v1.8.0` from the
# repository root. The tool will:
#   1. refuse to run on a dirty working tree;
#   2. run the full local verification (contracts, API, ops, web);
#   3. refuse to run if any check fails;
#   4. update CHANGELOG.md with a fresh "Unreleased" entry that
#      you can edit before committing;
#   5. commit, tag, push, and create a GitHub release whose body
#      is the new CHANGELOG section.
#
# `gh` and the matching `origin` remote are required for steps 4-5.

VERSION ?=
GITHUB_REPO ?=

.PHONY: help check release release-dry-run

help:
	@echo "targets:"
	@echo "  make check         - run all offline verifiers (with live DB+GROBID)"
	@echo "  make test          - run the offline unit tests only (no DB+GROBID)"
	@echo "  make release       - bump VERSION, tag, push, gh release create"
	@echo "  make release-dry-run - show the would-be release steps without changing anything"

check:
	@echo "== validate_package =="
	uv run --no-project --with pyyaml --with jsonschema --with openapi-spec-validator \
	    python scripts/validate_package.py
	@echo "== validate_eval_assets =="
	uv run --no-project --with pyyaml \
	    python scripts/validate_eval_assets.py
	@echo "== API lint =="
	cd starter/services/api && ../../services/api/.venv/bin/ruff check src tests
	@echo "== API typecheck =="
	cd starter/services/api && ../../services/api/.venv/bin/mypy src
	@echo "== API tests =="
	cd starter/services/api && \
	    CITETRACE_PGVECTOR_URL=$${CITETRACE_PGVECTOR_URL:-postgresql://citetrace:citetrace@localhost:55445/citetrace} \
	    CITETRACE_DATABASE_URL=$${CITETRACE_DATABASE_URL:-postgresql://citetrace:citetrace@localhost:55445/citetrace} \
	    ../../services/api/.venv/bin/pytest -q tests || \
	    (uv pip install --python .venv/bin/python -e '.[dev]' && ../../services/api/.venv/bin/pytest -q tests)
	@echo "== Ops tests =="
	cd starter/ops && ../services/api/.venv/bin/pytest tests -q
	@echo "== Helm lint =="
	@if command -v helm >/dev/null 2>&1; then \
	    helm lint starter/ops/release/helm; \
	else \
	    echo "(helm not installed; skipping helm lint per ADR-0014)"; \
	fi
	@echo "== Helm kubeconform =="
	@if command -v helm >/dev/null 2>&1 && command -v kubeconform >/dev/null 2>&1; then \
	    helm template citetrace starter/ops/release/helm \
	        | kubeconform -summary -strict -kubernetes-version 1.30.0 -; \
	else \
	    echo "(helm or kubeconform not installed; skipping kubeconform gate)"; \
	fi
	@echo "== Secret rotation check =="
	@echo "(skipped by default; override per ADR-0015 with CITETRACE_SECRET_AGE_<NAME> values)"
	@echo "== Web typecheck =="
	cd starter/apps/web && pnpm typecheck
	@echo "== Web build =="
	cd starter/apps/web && pnpm build

# `make test` is the offline unit-test fast path. It runs the
# API + ops + web tests with CITETRACE_PGVECTOR_URL and
# CITETRACE_DATABASE_URL unset so the DB-dependent tests
# skip cleanly. It does NOT run the contract validators,
# the helm lint, the web build, or any live smoke.
test:
	@echo "== API tests (offline) =="
	cd starter/services/api && \
	    env -u CITETRACE_PGVECTOR_URL -u CITETRACE_DATABASE_URL -u CITETRACE_GROBID_URL \
	    ../../services/api/.venv/bin/pytest -q tests
	@echo "== Ops tests =="
	cd starter/ops && \
	    env -u CITETRACE_PGVECTOR_URL -u CITETRACE_DATABASE_URL \
	    ../services/api/.venv/bin/pytest tests -q
	@echo "== Web unit tests =="
	cd starter/apps/web && pnpm test

release-dry-run:
	@echo "VERSION=$(VERSION)  GITHUB_REPO=$(GITHUB_REPO)"
	@echo "would run: make check"
	@echo "would update CHANGELOG.md"
	@echo "would commit, tag $(VERSION), push, gh release create $(VERSION)"

release:
	@if [ -z "$(VERSION)" ]; then \
	    echo "VERSION is required, e.g. make release VERSION=v1.8.0"; exit 2; \
	fi
	@if [ -n "$$(git status --porcelain)" ]; then \
	    echo "working tree is dirty; commit or stash first"; exit 2; \
	fi
	@if [ -z "$$(git tag -l $(VERSION))" ]; then \
	    echo "tag $(VERSION) does not exist locally; refusing to publish a tag the user did not author"; \
	    echo "create the tag with: git tag -a $(VERSION) -m '...'"; exit 2; \
	fi
	@if ! command -v gh >/dev/null 2>&1; then \
	    echo "gh CLI is required for the release step"; exit 2; \
	fi
	@echo "== running check =="
	@$(MAKE) --no-print-directory check
	@echo "== pushing tag $(VERSION) =="
	git push origin $(VERSION)
	@echo "== creating GitHub release $(VERSION) =="
	gh release create $(VERSION) \
	    --title "CiteTrace $(VERSION)" \
	    --notes-file CHANGELOG.md \
	    $(if $(GITHUB_REPO),--repo $(GITHUB_REPO),)

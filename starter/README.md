# CiteTrace executable foundation

This directory is a runnable foundation for validating repository conventions, API contracts, state transitions, quote integrity and the reader layout. It is deliberately not presented as the completed scientific-analysis product. Before implementation merge, generate and commit trustworthy dependency lockfiles according to `DEPENDENCY_LOCKING.md`.

Implemented in the scaffold:

- FastAPI health, create/get/cancel/list/stream analysis endpoints,
- idempotent in-memory analysis store,
- closed domain enums and transition guards,
- exact quote/offset validator,
- tests for API behavior, idempotency, transitions and quote integrity,
- Next.js three-pane evidence reader shell,
- local PostgreSQL/pgvector, Redis and GROBID services,
- CI workflow for Python tests, schema checks and web type/build checks.

Still implemented through the milestone plans rather than this scaffold:

- secure upload/object storage,
- GROBID TEI normalization,
- provider adapters and reference resolution,
- lawful source acquisition,
- hybrid retrieval and reranking,
- model gateway, relation verifier and explanation auditor,
- PostgreSQL repositories, authentication and full RLS transaction context,
- production deployment and observability.

## Local API

```bash
cp .env.example .env
docker compose up -d postgres redis grobid
make api-install
make api-test
make api-dev
```

API docs: `http://localhost:8000/docs`  
Health: `http://localhost:8000/healthz`

## Local web

```bash
corepack enable
pnpm --dir apps/web install
pnpm --dir apps/web dev
```

Web: `http://localhost:3000`

## Contract validation

From the package root:

```bash
python scripts/validate_package.py
```

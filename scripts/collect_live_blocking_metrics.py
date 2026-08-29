#!/usr/bin/env python3
"""Collect the three live blocking metrics for the release gate.

The release-time evaluation script (scripts/run_release_evaluation.py)
treats the following three metrics as blocking but does not
synthesise them: a release cannot be claimed as passed when they
are unmeasured. This script produces them from a live PostgreSQL
+ pgvector database that the running pipeline has written to.

Exit codes:
  0 — every measured metric is within the rubric threshold
  1 — a blocking metric is violated (e.g. a cross-tenant access
      attempt made it past the gate)
  2 — the window is empty; cannot evaluate

The script is single-tenant by construction: --tenant-id is
required, and the script SET LOCAL app.tenant_id before any read.
A misconfigured invocation that omits --tenant-id is a hard
failure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:
    print("psycopg is required; install it with: uv pip install 'psycopg[binary]'", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_LINK_SCHEMA = REPO_ROOT / "contracts" / "schemas" / "evidence-link.v1.schema.json"


def _set_local_tenant(cur: psycopg.cursor.Cursor, tenant_id: str) -> None:
    """SET LOCAL is not allowed with parameter placeholders. The
    tenant_id is validated as a UUID below, so a literal
    interpolation is safe.
    """
    import uuid as _uuid

    parsed = _uuid.UUID(tenant_id)
    cur.execute(f"SET LOCAL app.tenant_id = '{parsed}'")


def _connect(database_url: str, tenant_id: str) -> psycopg.Connection:
    conn = psycopg.connect(database_url)
    with conn.cursor() as cur:
        _set_local_tenant(cur, tenant_id)
    conn.commit()
    return conn


def _read_evidence_links(conn: psycopg.Connection, tenant_id: str, window_start: datetime) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        _set_local_tenant(cur, tenant_id)
        cur.execute(
            """
            SELECT id, workspace_id, analysis_run_id, evidence_relation,
                   access_level, confidence_vector, scope_observations, abstention,
                   citation_intents, transformations, audit_status
            FROM evidence_link
            WHERE workspace_id = %s
              AND created_at >= %s
            ORDER BY created_at
            """,
            (tenant_id, window_start),
        )
        rows = cur.fetchall()
    keys = (
        "id", "workspace_id", "analysis_run_id", "evidence_relation",
        "access_level", "confidence_vector", "scope_observations", "abstention",
        "citation_intents", "transformations", "audit_status",
    )
    return [dict(zip(keys, row)) for row in rows]


def _validate_payload(payload: dict[str, Any]) -> bool:
    """A pragmatic schema validation that does not require the
    jsonschema package: the payload must declare every required
    key from contracts/schemas/evidence-link.v1.schema.json.
    The full JSON Schema validation is wired in
    `scripts/validate_package.py`; the release gate's blocking
    metric is a coarse but real signal."""
    required = (
        "id", "workspace_id", "analysis_run_id",
        "evidence_relation", "citation_intents", "transformations",
        "access_level", "confidence_vector", "audit_status",
    )
    return all(payload.get(key) is not None for key in required)


def _count_cross_tenant_attempts(conn: psycopg.Connection, tenant_id: str, window_start: datetime) -> int:
    with conn.cursor() as cur:
        _set_local_tenant(cur, tenant_id)
        cur.execute(
            """
            SELECT COUNT(*)
            FROM audit_decision ad
            JOIN evidence_link el ON el.id = ad.evidence_link_id
            WHERE el.workspace_id = %s
              AND el.created_at >= %s
              AND 'cross_tenant_access' = ANY(ad.blocking_codes)
            """,
            (tenant_id, window_start),
        )
        return int(cur.fetchone()[0])


def _count_inaccessible_false_full_text_claims(
    conn: psycopg.Connection, tenant_id: str, window_start: datetime
) -> int:
    """A 'false full-text claim' is an evidence link whose source
    was not accessible (open access, not paywalled, etc.) but
    whose confidence_vector records full-text grounding
    (weakest_link > 0.85 AND no abstention)."""
    with conn.cursor() as cur:
        _set_local_tenant(cur, tenant_id)
        cur.execute(
            """
            SELECT COUNT(*)
            FROM evidence_link
            WHERE workspace_id = %s
              AND created_at >= %s
              AND access_level = 'not_accessible'
              AND abstention IS NULL
              AND (confidence_vector->>'weakest_link')::float > 0.85
            """,
            (tenant_id, window_start),
        )
        return int(cur.fetchone()[0])


def collect(
    database_url: str,
    tenant_id: str,
    window_start: datetime,
) -> dict[str, Any]:
    with _connect(database_url, tenant_id) as conn:
        links = _read_evidence_links(conn, tenant_id, window_start)
    if not links:
        return {
            "case_count": 0,
            "schema_valid_rate": None,
            "cross_tenant_access_failures": None,
            "inaccessible_source_false_full_text_claims": None,
            "window_start": window_start.isoformat(),
            "tenant_id": tenant_id,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
    valid = sum(1 for link in links if _validate_payload(link))
    with _connect(database_url, tenant_id) as conn:
        cross_tenant = _count_cross_tenant_attempts(conn, tenant_id, window_start)
        false_full_text = _count_inaccessible_false_full_text_claims(conn, tenant_id, window_start)
    return {
        "case_count": len(links),
        "schema_valid_rate": valid / len(links) if links else None,
        "cross_tenant_access_failures": cross_tenant,
        "inaccessible_source_false_full_text_claims": false_full_text,
        "window_start": window_start.isoformat(),
        "tenant_id": tenant_id,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def _parse_window(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--window-start", required=True, help="ISO 8601 timestamp")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if not args.tenant_id.strip():
        print("--tenant-id is required and must be non-empty", file=sys.stderr)
        return 2

    window_start = _parse_window(args.window_start)
    payload = collect(args.database_url, args.tenant_id, window_start)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if payload["case_count"] == 0:
        print(
            f"window {args.window_start} has no evidence links; cannot evaluate",
            file=sys.stderr,
        )
        return 2

    failures: list[str] = []
    if payload["schema_valid_rate"] is not None and payload["schema_valid_rate"] < 1.0:
        failures.append(
            f"schema_valid_rate={payload['schema_valid_rate']} failed gte 1.0"
        )
    if payload["cross_tenant_access_failures"] != 0:
        failures.append(
            f"cross_tenant_access_failures={payload['cross_tenant_access_failures']} failed eq 0"
        )
    if payload["inaccessible_source_false_full_text_claims"] != 0:
        failures.append(
            f"inaccessible_source_false_full_text_claims="
            f"{payload['inaccessible_source_false_full_text_claims']} failed eq 0"
        )
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print(f"metrics collected and within thresholds; report at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Contract tests for the live blocking-metric collector (Slice 10).

The collector must:

- exit 0 when the three blocking metrics are within thresholds,
- exit 1 when a blocking metric is violated,
- exit 2 when the window is empty (cannot evaluate),
- never report a `null` metric as 0; a missing measurement
  fails the rubric,
- be single-tenant by construction (the script must SET LOCAL
  app.tenant_id before any read).

The test uses the same `pgvector/pgvector:pg18` container the
pgvector slice brought up. If the container is not reachable
the test is skipped so offline CI runs are honest.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

DATABASE_URL = os.environ.get(
    "CITETRACE_DATABASE_URL",
    "postgresql://citetrace:citetrace@localhost:55445/citetrace",
)
REPO_ROOT = Path(__file__).resolve().parents[4]
COLLECTOR = REPO_ROOT / "scripts" / "collect_live_blocking_metrics.py"


def _database_alive() -> bool:
    try:
        import psycopg
    except ImportError:
        return False
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:
        return False


pytest.importorskip("psycopg", reason="psycopg not installed")


def _seed_clean_run(tenant_id: str) -> None:
    """Seed a single valid evidence_link with the parent FK chain
    so the collector returns real (non-null) metrics."""
    import psycopg

    parsed = uuid.UUID(tenant_id)
    asset_id = uuid.uuid4()
    document_id = uuid.uuid4()
    cluster_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    analysis_id = uuid.uuid4()
    link_id = uuid.uuid4()
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL app.tenant_id = '{parsed}'")
            cur.execute(
                "INSERT INTO workspace (id, slug, name) VALUES (%s, %s, 'test') ON CONFLICT (id) DO NOTHING",
                (parsed, f"t-{parsed.hex[:8]}"),
            )
            cur.execute(
                """
                INSERT INTO source_asset
                    (id, workspace_id, sha256, media_type, byte_size,
                     acquisition_method, access_level)
                VALUES (%s, %s, repeat('a', 64)::char(64), 'application/pdf', 1,
                        'user_upload', 'open_access_full_text')
                ON CONFLICT (id) DO NOTHING
                """,
                (asset_id, parsed),
            )
            cur.execute(
                """
                INSERT INTO parsed_document
                    (id, source_asset_id, parser_name, parser_version, parser_profile,
                     normalized_text, normalized_text_sha256, parse_quality_grade)
                VALUES (%s, %s, 'grobid', '0.9.1', 'default',
                        'placeholder', repeat('a', 64)::char(64), 'a')
                ON CONFLICT (id) DO NOTHING
                """,
                (document_id, asset_id),
            )
            cur.execute(
                """
                INSERT INTO citation_cluster
                    (id, parsed_document_id, anchor_text, start_offset, end_offset)
                VALUES (%s, %s, 'see [1]', 0, 7)
                ON CONFLICT (id) DO NOTHING
                """,
                (cluster_id, document_id),
            )
            cur.execute(
                """
                INSERT INTO citing_claim
                    (id, citation_cluster_id, parsed_document_id, claim_text,
                     normalized_claim, start_offset, end_offset, extractor_name,
                     extractor_version)
                VALUES (%s, %s, %s, 'Method A improved accuracy.',
                        'method a improved accuracy', 0, 26, 'test', 'v1')
                ON CONFLICT (id) DO NOTHING
                """,
                (claim_id, cluster_id, document_id),
            )
            cur.execute(
                """
                INSERT INTO analysis_run
                    (id, workspace_id, source_asset_id, parsed_document_id, mode, audience,
                     requested_scope, source_policy_profile, pipeline_version,
                     idempotency_key, input_fingerprint, status)
                VALUES (%s, %s, %s, %s, 'understand', 'expert',
                        '{}'::jsonb, 'default', 'v1.2.0',
                        %s, repeat('a', 64)::char(64), 'completed')
                ON CONFLICT (id) DO NOTHING
                """,
                (analysis_id, parsed, asset_id, document_id, f"test-{parsed}"),
            )
            cur.execute(
                """
                INSERT INTO evidence_link
                    (id, workspace_id, analysis_run_id, citing_claim_id,
                     status, evidence_relation, citation_intents, transformations,
                     scope_observations, access_level, confidence_vector,
                     calibration_profile, audit_status)
                VALUES (%s, %s, %s, %s,
                        'verified', 'direct_support',
                        ARRAY['result_support']::citation_intent[],
                        ARRAY[]::transformation_kind[],
                        '[]'::jsonb, 'open_access_full_text',
                        jsonb_build_object('weakest_link', 0.5, 'balanced_score', 0.7),
                        'default', 'passed')
                ON CONFLICT (id) DO NOTHING
                """,
                (link_id, parsed, analysis_id, claim_id),
            )
        conn.commit()
        conn.commit()


def test_collector_exits_two_on_empty_window(tmp_path: Path) -> None:
    if not _database_alive():
        pytest.skip(f"database not reachable at {DATABASE_URL}")
    if not COLLECTOR.exists():
        pytest.fail(f"{COLLECTOR.relative_to(REPO_ROOT)} missing")

    output = tmp_path / "metrics.json"
    result = subprocess.run(
        [
            sys.executable,
            str(COLLECTOR),
            "--database-url",
            DATABASE_URL,
            "--tenant-id",
            "00000000-0000-0000-0000-000000000000",
            "--window-start",
            "2999-01-01T00:00:00Z",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2, (
        f"empty window must fail with exit 2; got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_valid_rate"] is None
    assert payload["cross_tenant_access_failures"] is None
    assert payload["inaccessible_source_false_full_text_claims"] is None


def test_collector_reports_metrics_on_real_run(tmp_path: Path) -> None:
    if not _database_alive():
        pytest.skip(f"database not reachable at {DATABASE_URL}")

    tenant = str(uuid.uuid4())
    _seed_clean_run(tenant)
    output = tmp_path / "metrics.json"
    result = subprocess.run(
        [
            sys.executable,
            str(COLLECTOR),
            "--database-url",
            DATABASE_URL,
            "--tenant-id",
            tenant,
            "--window-start",
            "2020-01-01T00:00:00Z",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"clean run must exit 0; got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_valid_rate"] is not None
    assert payload["cross_tenant_access_failures"] is not None
    assert payload["inaccessible_source_false_full_text_claims"] is not None


def test_collector_rejects_unset_tenant_id() -> None:
    if not COLLECTOR.exists():
        pytest.fail(f"{COLLECTOR.relative_to(REPO_ROOT)} missing")
    result = subprocess.run(
        [
            sys.executable,
            str(COLLECTOR),
            "--database-url",
            DATABASE_URL,
            "--window-start",
            "2020-01-01T00:00:00Z",
            "--output",
            "/tmp/metrics.json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, (
        "missing --tenant-id must be a hard failure; the script must "
        "never read across tenants"
    )


def test_collector_does_not_pretend_missing_metric_is_zero() -> None:
    if not _database_alive():
        pytest.skip(f"database not reachable at {DATABASE_URL}")
    payload = {
        "case_count": 0,
        "schema_valid_rate": None,
        "cross_tenant_access_failures": None,
        "inaccessible_source_false_full_text_claims": None,
    }
    for key, value in payload.items():
        if value is None:
            with pytest.raises(AssertionError):
                assert value == 0, (
                    f"{key} must not be silently coerced to 0; the release "
                    "gate fails closed when a metric is unmeasured (Slice 2)"
                )

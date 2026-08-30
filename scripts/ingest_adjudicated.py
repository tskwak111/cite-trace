#!/usr/bin/env python3
"""Ingest adjudicated.jsonl records into the CiteTrace PostgreSQL DB.

Usage:
    python scripts/ingest_adjudicated.py \\
        --input evaluation/adjudicated.jsonl \\
        --database-url postgresql://citetrace:citetrace@localhost:55448/citetrace

Environment:
    CITETRACE_ADJUDICATED_JSONL  path to adjudicated.jsonl (default: evaluation/adjudicated.jsonl)
    CITETRACE_DATABASE_URL        PostgreSQL connection URL
    CITETRACE_AUTH_SECRET         required by dependency resolution (unused in this script)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from typing import Any

import psycopg
from pydantic import BaseModel, Field, field_validator


class AdjudicatedRecord(BaseModel):
    analysis_id: uuid.UUID
    workspace_id: uuid.UUID
    citing_asset_id: uuid.UUID
    citing_claim_span: str
    cited_external_ids: dict[str, str] = Field(default_factory=dict)
    evidence_relation: str
    citation_intents: list[str] = Field(default_factory=list)
    transformations: list[str] = Field(default_factory=list)
    confidence_vector: dict[str, float] = Field(default_factory=dict)
    calibration_profile: str = "default"
    status: str = "review_required"
    access_level: str = "user_private_full_text"
    model_execution_ids: list[uuid.UUID] = Field(default_factory=list)

    @field_validator("evidence_relation")
    @classmethod
    def _check_relation(cls, v: str) -> str:
        valid = {
            "direct_support", "partial_support", "indirect_support",
            "contradicts", "overgeneralized", "scope_mismatch",
            "no_relevant_evidence", "insufficient_evidence",
            "inaccessible_source",
        }
        if v not in valid:
            raise ValueError(f"unknown evidence_relation {v!r}")
        return v


def resolve_work_version(conn: psycopg.Connection, external_ids: dict[str, str]) -> tuple[uuid.UUID, uuid.UUID] | None:
    doi = external_ids.get("doi", "").strip()
    title = external_ids.get("title", "").strip()
    if not doi and not title:
        return None
    if doi:
        result = conn.execute(
            """
            SELECT w.id, wv.id
            FROM citetrace.scholarly_work w
            JOIN citetrace.work_version wv ON wv.work_id = w.id
            WHERE w.identifiers->>'doi' = %s
            LIMIT 1
            """,
            (doi,),
        ).fetchone()
        if result:
            return (uuid.UUID(result[0]), uuid.UUID(result[1]))
    if title:
        result = conn.execute(
            """
            SELECT w.id, wv.id
            FROM citetrace.scholarly_work w
            JOIN citetrace.work_version wv ON wv.work_id = w.id
            WHERE w.normalized_title = citetrace.normalize_title(%s)
            LIMIT 1
            """,
            (title,),
        ).fetchone()
        if result:
            return (uuid.UUID(result[0]), uuid.UUID(result[1]))
    return None


def upsert_evidence_link(conn: psycopg.Connection, rec: AdjudicatedRecord, cited_work_id: uuid.UUID | None, cited_version_id: uuid.UUID | None) -> None:
    evidence_id = conn.execute(
        """
        SELECT id FROM citetrace.evidence_link
        WHERE analysis_run_id = %s AND citing_claim_id IN (
            SELECT id FROM citetrace.citing_claim WHERE source_asset_id = %s AND claim_text = %s
        )
        LIMIT 1
        """,
        (rec.analysis_id, rec.citing_asset_id, rec.citing_claim_span),
    ).fetchone()

    if evidence_id:
        conn.execute(
            """
            UPDATE citetrace.evidence_link SET
                evidence_relation = %s,
                citation_intents = %s,
                transformations = %s,
                confidence_vector = %s,
                calibration_profile = %s,
                status = %s,
                access_level = %s,
                updated_at = now()
            WHERE id = %s
            """,
            (
                rec.evidence_relation,
                rec.citation_intents,
                rec.transformations,
                json.dumps(rec.confidence_vector),
                rec.calibration_profile,
                rec.status,
                rec.access_level,
                evidence_id[0],
            ),
        )
    else:
        citing_claim_id = conn.execute(
            """
            INSERT INTO citetrace.citing_claim (id, source_asset_id, claim_text, created_at)
            VALUES (%s, %s, %s, now())
            ON CONFLICT DO NOTHING
            RETURNING id
            """,
            (uuid.uuid4(), rec.citing_asset_id, rec.citing_claim_span),
        ).fetchone()
        if citing_claim_id is None:
            citing_claim_id = conn.execute(
                "SELECT id FROM citetrace.citing_claim WHERE source_asset_id = %s AND claim_text = %s",
                (rec.citing_asset_id, rec.citing_claim_span),
            ).fetchone()

        conn.execute(
            """
            INSERT INTO citetrace.evidence_link (
                id, workspace_id, analysis_run_id, citing_claim_id,
                cited_work_version_id, evidence_relation, citation_intents,
                transformations, confidence_vector, calibration_profile,
                status, access_level, model_execution_ids, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()
            )
            ON CONFLICT (id) DO UPDATE SET
                evidence_relation = EXCLUDED.evidence_relation,
                citation_intents = EXCLUDED.citation_intents,
                transformations = EXCLUDED.transformations,
                confidence_vector = EXCLUDED.confidence_vector,
                calibration_profile = EXCLUDED.calibration_profile,
                status = EXCLUDED.status,
                access_level = EXCLUDED.access_level,
                updated_at = now()
            """,
            (
                uuid.uuid4(),
                rec.workspace_id,
                rec.analysis_id,
                citing_claim_id[0],
                cited_version_id,
                rec.evidence_relation,
                rec.citation_intents,
                rec.transformations,
                json.dumps(rec.confidence_vector),
                rec.calibration_profile,
                rec.status,
                rec.access_level,
                [str(x) for x in rec.model_execution_ids],
            ),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest adjudicated.jsonl into CiteTrace DB")
    parser.add_argument("--input", default="evaluation/adjudicated.jsonl")
    parser.add_argument("--database-url", default="postgresql://citetrace:citetrace@localhost:5432/citetrace")
    args = parser.parse_args()

    env_db = os.environ.get("CITETRACE_DATABASE_URL", "")
    database_url = env_db or args.database_url

    input_path = Path(os.environ.get("CITETRACE_ADJUDICATED_JSONL", args.input))

    records: list[AdjudicatedRecord] = []
    skipped = 0
    errors = 0

    with open(input_path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(AdjudicatedRecord(**data))
            except Exception as exc:
                print(f"WARNING: line {lineno}: {exc}", file=sys.stderr)
                errors += 1

    if not records:
        print("Nothing to ingest.")
        return

    print(f"Loaded {len(records)} records ({errors} parse errors). Connecting to DB...")

    try:
        conn = psycopg.connect(database_url)
    except Exception as exc:
        print(f"ERROR: cannot connect to DB: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        imported = 0
        skipped_resolve = 0
        for rec in records:
            cited = resolve_work_version(conn, rec.cited_external_ids)
            if cited is None and rec.cited_external_ids:
                print(f"  WARNING: cannot resolve {rec.cited_external_ids}", file=sys.stderr)
                skipped_resolve += 1
                continue
            cited_work_id, cited_version_id = cited if cited else (None, None)
            upsert_evidence_link(conn, rec, cited_work_id, cited_version_id)
            imported += 1
        conn.commit()
        print(f"\nIngested {imported} records ({skipped_resolve} skipped - unresolved work).")
        print(f"Total: {len(records)} loaded, {errors} parse errors, {skipped} skipped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

"""Sync test: keep the canonical schema in lockstep with the migration copy.

`contracts/db/schema.sql` is the single source of truth for the v1
PostgreSQL contract (per `contracts/db/README.md`). The file at
`starter/services/api/migrations/0001_initial.sql` is a byte-for-byte
copy so that migration runners (alembic, yoyo-migrations, sqitch) can
discover the schema under the deployment's migrations directory.

This test fails if the two files drift, which would mean a schema
change was applied to one location and forgotten in the other.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
CANONICAL = REPO_ROOT / "contracts" / "db" / "schema.sql"
MIGRATION = (
    REPO_ROOT
    / "starter"
    / "services"
    / "api"
    / "migrations"
    / "0001_initial.sql"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_canonical_schema_exists() -> None:
    assert CANONICAL.exists(), f"missing canonical schema at {CANONICAL}"


def test_migration_copy_exists() -> None:
    assert MIGRATION.exists(), f"missing migration copy at {MIGRATION}"


def test_schema_files_are_in_sync() -> None:
    canonical = _sha256(CANONICAL)
    migration = _sha256(MIGRATION)
    assert canonical == migration, (
        "schema drift detected: contracts/db/schema.sql and "
        "starter/services/api/migrations/0001_initial.sql differ. "
        "Both must be updated together; see ADR-0008 Slice 1."
    )


@pytest.mark.parametrize(
    "path",
    [CANONICAL, MIGRATION],
    ids=["canonical", "migration_copy"],
)
def test_schema_is_not_empty(path: Path) -> None:
    assert path.stat().st_size > 1024, (
        f"{path} is suspiciously small ({path.stat().st_size} bytes); "
        "did a placeholder get committed?"
    )

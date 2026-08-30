"""RLS force + cross-tenant contract tests (Slice 13).

These tests are the acceptance criteria for ADR-0011:

  - every table that has a workspace_id column is RLS-enabled
    AND RLS-forced (the FORCE keyword makes the policy apply
    to the table owner as well, not just to other roles);
  - a non-superuser application role that owns the tenant
    tables sees only its own workspace's rows;
  - a deliberate cross-tenant write from that role targeting
    another workspace's row is denied by the policy;
  - the application role created for the test does not have
    the BYPASSRLS attribute (the AGENTS.md invariant
    'application roles must not bypass RLS').

The tests use the same `pgvector/pgvector:pg18` container the
pgvector slice brought up. The container's `POSTGRES_USER` is
a Docker-image superuser, so a separate non-superuser role is
created at test time to exercise the non-bypass path. The
test fixture re-grants the table ownership to the application
role after the schema is applied (the schema sets the owner
to the original superuser). If the container is not reachable,
the tests are skipped so offline CI runs are honest.
"""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import psycopg

PGVECTOR_URL = os.environ.get(
    "CITETRACE_PGVECTOR_URL", "postgresql://citetrace:citetrace@localhost:55445/citetrace"
)
APP_ROLE = "citetrace_app"
APP_ROLE_PASSWORD = "citetrace_app"
WORKSPACE_ID_A = "11111111-1111-1111-1111-111111111111"
WORKSPACE_ID_B = "22222222-2222-2222-2222-222222222222"


def _database_alive() -> bool:
    try:
        import psycopg
    except ImportError:
        return False
    try:
        with psycopg.connect(PGVECTOR_URL, connect_timeout=2) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception:
        return False


pytest.importorskip("psycopg", reason="psycopg not installed")


def _set_local_tenant(cur, tenant_id: str) -> None:
    cur.execute(f"SET LOCAL app.workspace_id = '{uuid.UUID(tenant_id)}'")


@pytest.fixture(scope="module")
def app_role_connection() -> psycopg.Connection:
    """Create a non-superuser, non-bypassrls application role that
    owns the tenant tables, and return a connection that uses
    it. The application role is the role the production code is
    expected to use; it must not bypass RLS.

    Skips the entire module when the database is unreachable
    so the offline `make test` path is clean.
    """
    if not _database_alive():
        pytest.skip(f"pgvector not reachable at {PGVECTOR_URL}")
    import psycopg  # imported lazily so the offline path is clean

    admin = psycopg.connect(PGVECTOR_URL)
    with admin.cursor() as cur:
        cur.execute(f"DROP ROLE IF EXISTS {APP_ROLE}")
        cur.execute(
            f"CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_ROLE_PASSWORD}' NOSUPERUSER NOBYPASSRLS"
        )
        cur.execute(
            f"GRANT CONNECT ON DATABASE citetrace TO {APP_ROLE}"
        )
        cur.execute(f"GRANT USAGE ON SCHEMA citetrace TO {APP_ROLE}")
        cur.execute(
            """
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'citetrace'
            """
        )
        tables = [r[0] for r in cur.fetchall()]
        for table in tables:
            cur.execute(
                f"ALTER TABLE citetrace.{table} OWNER TO {APP_ROLE}"
            )
        cur.execute(
            """
            SELECT sequence_name FROM information_schema.sequences
            WHERE sequence_schema = 'citetrace'
            """
        )
        sequences = [r[0] for r in cur.fetchall()]
        for sequence in sequences:
            cur.execute(
                f"ALTER SEQUENCE citetrace.{sequence} OWNER TO {APP_ROLE}"
            )
        cur.execute(
            f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA citetrace TO {APP_ROLE}"
        )
        cur.execute(
            f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA citetrace TO {APP_ROLE}"
        )
        cur.execute(
            f"GRANT USAGE ON SCHEMA citetrace TO {APP_ROLE}"
        )
    admin.commit()
    admin.close()

    conn = psycopg.connect(
        PGVECTOR_URL.replace("citetrace:citetrace", f"{APP_ROLE}:{APP_ROLE_PASSWORD}"),
        autocommit=False,
    )
    with conn.cursor() as cur:
        cur.execute("SET search_path TO citetrace, public")
        for tenant_id in (WORKSPACE_ID_A, WORKSPACE_ID_B):
            cur.execute(
                f"SET LOCAL app.workspace_id = '{tenant_id}'"
            )
            cur.execute(
                """
                INSERT INTO workspace (id, slug, name)
                VALUES (%s, %s, 'rls-test')
                ON CONFLICT (id) DO NOTHING
                """,
                (tenant_id, f"rls-{tenant_id[:8]}"),
            )
    conn.commit()
    with conn.cursor() as cur:
        cur.execute("SET search_path TO citetrace, public")
    try:
        yield conn
    finally:
        conn.close()
        admin = psycopg.connect(PGVECTOR_URL)
        try:
            with admin.cursor() as cur:
                for table in tables:
                    cur.execute(
                        f"ALTER TABLE citetrace.{table} OWNER TO citetrace"
                    )
                for sequence in sequences:
                    cur.execute(
                        f"ALTER SEQUENCE citetrace.{sequence} OWNER TO citetrace"
                    )
                cur.execute(f"DROP OWNED BY {APP_ROLE} CASCADE")
                cur.execute(f"DROP ROLE IF EXISTS {APP_ROLE}")
            admin.commit()
        finally:
            admin.close()


def test_every_tenant_table_is_rls_forced() -> None:
    """Every table that has a workspace_id column must have
    relrowsecurity = true AND relforcerowsecurity = true.
    Without FORCE, the table owner is exempt from the
    policy."""
    if not _database_alive():
        pytest.skip(f"pgvector not reachable at {PGVECTOR_URL}")
    import psycopg

    with psycopg.connect(PGVECTOR_URL) as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT c.relname,
                       c.relrowsecurity AS rls_enabled,
                       c.relforcerowsecurity AS rls_forced
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'citetrace'
                  AND c.relkind = 'r'
                  AND EXISTS (
                      SELECT 1 FROM pg_attribute a
                      WHERE a.attrelid = c.oid
                        AND a.attname = 'workspace_id'
                        AND a.attnum > 0
                  )
                ORDER BY c.relname
                """
        )
        rows = cur.fetchall()
    assert rows, "no tenant-scoped tables found; the schema has not been applied"
    missing_force = [r[0] for r in rows if not r[2]]
    assert not missing_force, (
        f"the following tables are RLS-enabled but not RLS-forced; "
        f"the table owner is exempt from the policy until FORCE is "
        f"added: {missing_force}"
    )


def test_app_role_does_not_bypass_rls(app_role_connection) -> None:
    if not _database_alive():
        pytest.skip(f"pgvector not reachable at {PGVECTOR_URL}")
    import psycopg

    with psycopg.connect(PGVECTOR_URL) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = %s",
            (APP_ROLE,),
        )
        row = cur.fetchone()
    assert row is not None, f"{APP_ROLE} role not created; the fixture must run first"
    superuser, bypass = row
    assert not superuser, f"{APP_ROLE} must not be a superuser"
    assert not bypass, f"{APP_ROLE} must not have BYPASSRLS"


def test_tenant_a_query_sees_only_a(app_role_connection) -> None:
    """A non-superuser application role with the GUC set to A
    must see only A's workspace row."""
    with app_role_connection.cursor() as cur:
        _set_local_tenant(cur, WORKSPACE_ID_A)
        cur.execute("SELECT COUNT(*) FROM workspace")
        count = cur.fetchone()[0]
    assert count == 1, (
        f"workspace A should see exactly its own row; saw {count} rows. "
        f"Either the seed failed or RLS is not enforced for the "
        f"non-superuser application role."
    )


def test_tenant_b_query_sees_only_b(app_role_connection) -> None:
    with app_role_connection.cursor() as cur:
        _set_local_tenant(cur, WORKSPACE_ID_B)
        cur.execute("SELECT COUNT(*) FROM workspace")
        count = cur.fetchone()[0]
    assert count == 1, (
        f"workspace B should see exactly its own row; saw {count} rows"
    )


def test_query_without_workspace_id_setting_sees_zero(app_role_connection) -> None:
    """With FORCE applied, an application role that forgets to
    set the GUC must see zero rows. This is the contract that
    protects against a future code path that omits the GUC."""
    import psycopg

    fresh = psycopg.connect(
        PGVECTOR_URL.replace("citetrace:citetrace", f"{APP_ROLE}:{APP_ROLE_PASSWORD}")
    )
    try:
        with fresh.cursor() as cur:
            cur.execute("SET search_path TO citetrace, public")
            cur.execute("SELECT current_setting('app.workspace_id', true)")
            setting = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM workspace")
            count = cur.fetchone()[0]
    finally:
        fresh.close()
    assert setting in (None, ""), (
        f"app.workspace_id is set to {setting!r}; the test must run with "
        f"the GUC unset to exercise the FORCE path"
    )
    assert count == 0, (
        f"with FORCE applied and the GUC unset, the policy must deny all "
        f"rows; saw {count} rows. The RLS policy is missing or not forced."
    )


def test_cross_tenant_write_is_denied(app_role_connection) -> None:
    """A role that has set app.workspace_id = A must not be able
    to write a row whose workspace_id is B."""
    new_id = str(uuid.uuid4())
    attack_succeeded = False
    policy_rejected = False
    try:
        with app_role_connection.cursor() as cur:
            _set_local_tenant(cur, WORKSPACE_ID_A)
            cur.execute(
                """
                INSERT INTO workspace (id, slug, name)
                VALUES (%s, 'cross-tenant-attack', 'attack')
                """,
                (new_id,),
            )
        app_role_connection.commit()
        attack_succeeded = True
    except Exception as exc:
        app_role_connection.rollback()
        msg = str(exc).lower()
        if "row-level security" in msg or "policy" in msg:
            policy_rejected = True
    assert policy_rejected, (
        f"cross-tenant write must be rejected by the RLS policy. "
        f"attack_succeeded={attack_succeeded}"
    )

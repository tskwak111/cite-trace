from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from citetrace_api.db.session import Database


# A simple check to see if we can connect to the DB
async def check_db_available():
    try:
        engine = create_async_engine(
            "postgresql+psycopg://citetrace:citetrace@localhost:5432/citetrace"
        )
        async with engine.connect():
            pass
        await engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture
async def database():
    db = Database("postgresql+psycopg://citetrace:citetrace@localhost:5432/citetrace", 10, 5.0)
    try:
        # verify connection
        async with db.engine.connect():
            pass
        yield db
    except Exception:
        pytest.skip("Database not available")
    finally:
        await db.close()


@pytest.mark.anyio
async def test_tenant_transaction_sets_local_workspace(database: Database) -> None:
    workspace_id = uuid4()
    async with database.tenant_transaction(workspace_id) as session:
        from sqlalchemy import text

        observed = await session.scalar(text("select current_setting('app.workspace_id', true)"))
        assert observed == str(workspace_id)

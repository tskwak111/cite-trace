from uuid import uuid4

import pytest

from citetrace_api.db.repositories.references import ReferenceRepository, WorkIdentity


@pytest.mark.anyio
async def test_upsert_work_identity():
    repo = ReferenceRepository()
    ident = WorkIdentity(id=uuid4(), title="Test Title")
    await repo.upsert_work_identity(ident)
    assert ident.id in repo._work_identities

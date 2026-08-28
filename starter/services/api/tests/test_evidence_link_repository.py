from uuid import uuid4

import pytest

from citetrace_api.db.repositories.evidence_links import EvidenceLinkRepository


@pytest.mark.anyio
async def test_evidence_link_repository():
    repo = EvidenceLinkRepository()
    link_id = uuid4()
    await repo.save_evidence_link(link_id, {"data": "test"})
    retrieved = await repo.get_evidence_link(link_id)
    assert retrieved == {"data": "test"}

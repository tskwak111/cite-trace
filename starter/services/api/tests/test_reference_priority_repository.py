from uuid import uuid4

import pytest

from citetrace_api.db.repositories.reference_priorities import ReferencePriorityRepository


@pytest.mark.anyio
async def test_reference_priority_repository():
    repo = ReferencePriorityRepository()
    analysis_id = uuid4()
    ref_id = uuid4()
    await repo.save_priority(analysis_id, ref_id, "understand", {"score": 0.9})
    retrieved = await repo.get_priority(analysis_id, ref_id, "understand")
    assert retrieved == {"score": 0.9}

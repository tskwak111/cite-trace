import uuid

from citetrace_api.retention.service import RetentionService


def test_tombstone_asset() -> None:
    service = RetentionService()
    asset_id = uuid.uuid4()
    assert service.tombstone_asset(asset_id) is True

def test_execute_deletion() -> None:
    service = RetentionService()
    asset_id = uuid.uuid4()
    assert service.execute_deletion(asset_id) is True

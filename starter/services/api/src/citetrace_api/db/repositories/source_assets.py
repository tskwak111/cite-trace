from datetime import UTC, datetime
from uuid import UUID


class SourceAsset:
    def __init__(
        self,
        id: UUID,
        workspace_id: UUID,
        work_version_id: UUID,
        access_level: str,
        acquisition_method: str,
        sha256: str | None = None,
        byte_size: int | None = None,
        object_key: str | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.workspace_id = workspace_id
        self.work_version_id = work_version_id
        self.access_level = access_level
        self.acquisition_method = acquisition_method
        self.sha256 = sha256
        self.byte_size = byte_size
        self.object_key = object_key
        self.created_at = created_at or datetime.now(UTC)


class SourceAssetRepository:
    def __init__(self, session: object = None) -> None:
        self.session = session
        self._in_memory_store: dict[UUID, SourceAsset] = {}

    async def get_by_work_version(
        self, workspace_id: UUID, work_version_id: UUID
    ) -> SourceAsset | None:
        # Mock implementation for tests
        for asset in self._in_memory_store.values():
            if asset.workspace_id == workspace_id and asset.work_version_id == work_version_id:
                return asset
        return None

    async def create(self, asset: SourceAsset) -> SourceAsset:
        self._in_memory_store[asset.id] = asset
        return asset

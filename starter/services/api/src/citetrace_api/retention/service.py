from uuid import UUID


class RetentionService:
    def __init__(self) -> None:
        pass

    def tombstone_asset(self, asset_id: UUID) -> bool:
        # Dummy implementation
        return True

    def execute_deletion(self, asset_id: UUID) -> bool:
        # Dummy implementation
        return True

import secrets
import uuid
import typing
from datetime import datetime, timedelta


class ShareService:
    def __init__(self) -> None:
        self._shares: dict[str, dict[str, typing.Any]] = {}

    async def create_share(self, target_id: str, permissions: list[str]) -> dict[str, typing.Any]:
        token = secrets.token_urlsafe(32)
        share_id = str(uuid.uuid4())
        self._shares[share_id] = {
            "id": share_id,
            "token": token,
            "target_id": target_id,
            "permissions": permissions,
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        return self._shares[share_id]

    async def resolve_share(self, token: str) -> dict[str, typing.Any]:
        for share in self._shares.values():
            if share["token"] == token and share["expires_at"] > datetime.utcnow():
                return {"status": "resolved", "target_id": share["target_id"]}
        raise ValueError("Invalid or expired token")

    async def revoke_share(self, share_id: str) -> bool:
        if share_id in self._shares:
            del self._shares[share_id]
            return True
        return False

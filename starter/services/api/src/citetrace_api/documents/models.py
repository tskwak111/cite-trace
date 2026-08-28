from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisteredSourceAsset:
    id: UUID
    workspace_id: UUID
    sha256: str
    media_type: str
    byte_size: int
    object_key: str
    access_level: str
    acquisition_method: str
    security_scan_status: str
    created_at: datetime
    retention_expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class RegisterUpload:
    workspace_id: UUID
    original_filename: str
    media_type: str
    data: bytes
    retention_expires_at: datetime

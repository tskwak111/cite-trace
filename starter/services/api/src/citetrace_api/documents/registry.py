from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from citetrace_api.documents.models import RegisteredSourceAsset, RegisterUpload
from citetrace_api.documents.pdf_validation import validate_pdf
from citetrace_api.documents.storage import ObjectStore, source_object_key


class DocumentRegistry:
    def __init__(self, store: ObjectStore) -> None:
        self.store = store

    async def register_upload(self, upload: RegisterUpload, session: AsyncSession | None = None) -> RegisteredSourceAsset:
        # 1. Validations
        report = validate_pdf(upload.data)
        if not report.accepted:
            raise ValueError(f"PDF validation failed: {report.code}")
            
        # 2. Hashing
        sha256 = hashlib.sha256(upload.data).hexdigest()
        
        # 3. Storage
        key = source_object_key(upload.workspace_id, sha256)
        await self.store.put_if_absent(key, upload.data, upload.media_type)
        
        # 4. Create model
        asset_id = uuid4()
        now = datetime.now(UTC)
        asset = RegisteredSourceAsset(
            id=asset_id,
            workspace_id=upload.workspace_id,
            sha256=sha256,
            media_type=upload.media_type,
            byte_size=len(upload.data),
            object_key=key,
            access_level='user_private_full_text',
            acquisition_method='user_upload',
            security_scan_status='clean',
            created_at=now,
            retention_expires_at=upload.retention_expires_at,
        )
        
        # 5. DB Persistence (if session provided)
        if session is not None:
            query = text("""
                INSERT INTO citetrace.source_asset (
                    id, workspace_id, sha256, media_type, byte_size,
                    object_key, access_level, acquisition_method,
                    security_scan_status, display_filename,
                    retention_expires_at, created_at, updated_at
                ) VALUES (
                    :id, :workspace_id, :sha256, :media_type, :byte_size,
                    :object_key, :access_level, :acquisition_method,
                    :security_scan_status, :display_filename,
                    :retention_expires_at, :created_at, :created_at
                )
            """)
            await session.execute(query, {
                "id": str(asset.id),
                "workspace_id": str(asset.workspace_id),
                "sha256": asset.sha256,
                "media_type": asset.media_type,
                "byte_size": asset.byte_size,
                "object_key": asset.object_key,
                "access_level": asset.access_level,
                "acquisition_method": asset.acquisition_method,
                "security_scan_status": asset.security_scan_status,
                "display_filename": upload.original_filename,
                "retention_expires_at": asset.retention_expires_at,
                "created_at": asset.created_at,
            })
            
        return asset

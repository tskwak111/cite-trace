from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class IdempotencyConflictError(Exception):
    """Raised when an operation with the same idempotency key has a different fingerprint."""


@dataclass(frozen=True, slots=True)
class NewAnalysis:
    workspace_id: UUID
    idempotency_key: str
    fingerprint: str
    document_id: UUID | None


@dataclass(frozen=True, slots=True)
class AnalysisRecord:
    id: UUID
    workspace_id: UUID
    idempotency_key: str
    fingerprint: str
    status: str
    created_at: datetime
    updated_at: datetime


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, analysis: NewAnalysis) -> AnalysisRecord:


        # We need to fetch the existing record first to check the fingerprint if we want to raise an error
        # A simple way is to insert DO NOTHING, then select.

        insert_query = text("""
            INSERT INTO citetrace.analysis_run (
                workspace_id, idempotency_key, fingerprint, status
            )
            VALUES (
                :workspace_id, :idempotency_key, :fingerprint, 'pending'
            )
            ON CONFLICT (workspace_id, idempotency_key) DO NOTHING
            RETURNING id, workspace_id, idempotency_key, fingerprint, status, created_at, updated_at
        """)

        params = {
            "workspace_id": str(analysis.workspace_id),
            "idempotency_key": analysis.idempotency_key,
            "fingerprint": analysis.fingerprint,
        }

        result = await self.session.execute(insert_query, params)
        row = result.fetchone()

        if row is None:
            # Conflict occurred and DO NOTHING triggered
            select_query = text("""
                SELECT id, workspace_id, idempotency_key, fingerprint, status, created_at, updated_at
                FROM citetrace.analysis_run
                WHERE workspace_id = :workspace_id AND idempotency_key = :idempotency_key
            """)
            result = await self.session.execute(select_query, params)
            row = result.fetchone()

            if row is not None and row.fingerprint != analysis.fingerprint:
                raise IdempotencyConflictError(
                    "Idempotency key already used with a different fingerprint"
                )

        if row is None:
            raise RuntimeError("Failed to create or retrieve analysis record")

        return AnalysisRecord(
            id=row.id,
            workspace_id=row.workspace_id,
            idempotency_key=row.idempotency_key,
            fingerprint=row.fingerprint,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get(self, analysis_id: UUID) -> AnalysisRecord | None:
        query = text("""
            SELECT id, workspace_id, idempotency_key, fingerprint, status, created_at, updated_at
            FROM citetrace.analysis_run
            WHERE id = :id
        """)
        result = await self.session.execute(query, {"id": str(analysis_id)})
        row = result.fetchone()
        if row is None:
            return None

        return AnalysisRecord(
            id=row.id,
            workspace_id=row.workspace_id,
            idempotency_key=row.idempotency_key,
            fingerprint=row.fingerprint,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def cancel(self, analysis_id: UUID) -> bool:
        query = text("""
            UPDATE citetrace.analysis_run
            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE id = :id AND status = 'pending'
            RETURNING id
        """)
        result = await self.session.execute(query, {"id": str(analysis_id)})
        row = result.fetchone()
        return row is not None

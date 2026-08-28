from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class NewOutboxEvent:
    aggregate_type: str
    aggregate_id: UUID
    event_type: str
    schema_version: str
    workspace_id: UUID
    payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class OutboxRecord:
    id: UUID
    aggregate_type: str
    aggregate_id: UUID
    event_type: str
    schema_version: str
    workspace_id: UUID
    payload: dict[str, object]
    status: str
    attempts: int
    created_at: datetime


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: NewOutboxEvent) -> UUID:
        event_id = uuid4()
        await self._session.execute(
            text("""
                INSERT INTO citetrace.outbox_event
                    (id, aggregate_type, aggregate_id, event_type, schema_version,
                     workspace_id, payload, status, attempts)
                VALUES
                    (:id, :aggregate_type, :aggregate_id, :event_type, :schema_version,
                     :workspace_id, :payload, 'pending', 0)
            """),
            {
                "id": event_id,
                "aggregate_type": event.aggregate_type,
                "aggregate_id": event.aggregate_id,
                "event_type": event.event_type,
                "schema_version": event.schema_version,
                "workspace_id": event.workspace_id,
                "payload": event.payload,
            },
        )
        return event_id

    async def claim_batch(self, worker_id: str, limit: int) -> list[OutboxRecord]:
        result = await self._session.execute(
            text("""
                SELECT id, aggregate_type, aggregate_id, event_type, schema_version,
                       workspace_id, payload, status, attempts, created_at
                FROM citetrace.outbox_event
                WHERE status IN ('pending', 'failed')
                  AND available_at <= now()
                ORDER BY created_at
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
            """),
            {"limit": limit},
        )
        rows = result.fetchall()
        records = []
        for row in rows:
            await self._session.execute(
                text("UPDATE citetrace.outbox_event SET attempts = attempts + 1 WHERE id = :id"),
                {"id": row.id},
            )
            records.append(
                OutboxRecord(
                    id=row.id,
                    aggregate_type=row.aggregate_type,
                    aggregate_id=row.aggregate_id,
                    event_type=row.event_type,
                    schema_version=row.schema_version,
                    workspace_id=row.workspace_id,
                    payload=dict(row.payload),
                    status=row.status,
                    attempts=row.attempts,
                    created_at=row.created_at,
                )
            )
        return records

    async def mark_published(self, event_id: UUID) -> None:
        await self._session.execute(
            text("""
                UPDATE citetrace.outbox_event
                SET status = 'published', published_at = now()
                WHERE id = :id
            """),
            {"id": event_id},
        )

    async def pending_for_aggregate(self, aggregate_id: UUID) -> list[OutboxRecord]:
        """For testing: get all pending events for an aggregate."""
        result = await self._session.execute(
            text("""
                SELECT id, aggregate_type, aggregate_id, event_type, schema_version,
                       workspace_id, payload, status, attempts, created_at
                FROM citetrace.outbox_event
                WHERE aggregate_id = :aggregate_id AND status = 'pending'
                ORDER BY created_at
            """),
            {"aggregate_id": aggregate_id},
        )
        rows = result.fetchall()
        return [
            OutboxRecord(
                id=row.id,
                aggregate_type=row.aggregate_type,
                aggregate_id=row.aggregate_id,
                event_type=row.event_type,
                schema_version=row.schema_version,
                workspace_id=row.workspace_id,
                payload=dict(row.payload),
                status=row.status,
                attempts=row.attempts,
                created_at=row.created_at,
            )
            for row in rows
        ]

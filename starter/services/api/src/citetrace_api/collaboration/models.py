from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Note(BaseModel):
    id: UUID
    workspace_id: UUID
    actor_user_id: UUID
    target_type: str
    target_id: UUID
    visibility: str
    markdown: str
    created_at: datetime
    idempotency_key: str

class CreateNote(BaseModel):
    workspace_id: UUID
    actor_user_id: UUID
    target_type: str
    target_id: UUID
    visibility: str
    markdown: str
    idempotency_key: str

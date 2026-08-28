import re
import uuid
from datetime import datetime

from .models import CreateNote, Note


def sanitize_markdown(markdown_text: str) -> str:
    # Strip script/iframe/unsafe tags
    sanitized = re.sub(r'<(script|iframe|object|embed|applet)[^>]*>.*?</>', '', markdown_text, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<(script|iframe|object|embed|applet)[^>]*>', '', sanitized, flags=re.IGNORECASE)
    return sanitized

class NotesService:
    def __init__(self) -> None:
        self._notes: list[Note] = []

    async def create_note(self, note_data: CreateNote) -> Note:
        sanitized_md = sanitize_markdown(note_data.markdown)
        note = Note(
            id=uuid.uuid4(),
            workspace_id=note_data.workspace_id,
            actor_user_id=note_data.actor_user_id,
            target_type=note_data.target_type,
            target_id=note_data.target_id,
            visibility=note_data.visibility,
            markdown=sanitized_md,
            created_at=datetime.utcnow(),
            idempotency_key=note_data.idempotency_key
        )
        self._notes.append(note)
        return note

    async def get_notes(self) -> list[Note]:
        return self._notes

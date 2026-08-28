import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from citetrace_api.streaming.event_store import EventStore, StreamEvent


def format_sse(event: StreamEvent) -> str:
    data = json.dumps(event.payload)
    return f"id: {event.id}\nevent: {event.event_type}\nretry: 3000\ndata: {data}\n\n"

def format_heartbeat() -> str:
    return ": heartbeat\n\n"

async def sse_stream(analysis_id: UUID, last_event_id: UUID | None, event_store: EventStore) -> AsyncIterator[str]:
    current_last_id = last_event_id
    current_sequence = 0
    
    while True:
        events = await event_store.after(analysis_id, current_last_id, limit=50)
        
        for event in events:
            yield format_sse(event)
            current_last_id = event.id
            current_sequence = event.sequence
            
            # terminal states
            if event.event_type in ("analysis.completed", "analysis.failed", "analysis.completed_with_limits"):
                return
        
        # wait for new events or timeout
        try:
            await asyncio.wait_for(
                event_store.wait_for_new(analysis_id, current_sequence, timeout_seconds=15.0),
                timeout=15.0
            )
        except TimeoutError:
            yield format_heartbeat()

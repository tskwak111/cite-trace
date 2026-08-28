import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import json
from unittest.mock import AsyncMock, patch, MagicMock

from citetrace_api.main import app
from citetrace_api.streaming.event_store import StreamEvent

WORKSPACE_ID = str(uuid4())
ANALYSIS_ID = str(uuid4())
FIRST_EVENT_ID = str(uuid4())
SECOND_EVENT_ID = str(uuid4())
THIRD_EVENT_ID = str(uuid4())
FOURTH_EVENT_ID = str(uuid4())

def auth_headers(workspace_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {workspace_id}"}

def parse_sse(text: str):
    events = []
    current_event = {}
    for line in text.splitlines():
        if line.startswith("id: "):
            current_event["id"] = line[4:]
        elif line.startswith("event: "):
            current_event["event"] = line[7:]
        elif line.startswith("data: "):
            current_event["data"] = line[6:]
        elif not line.strip() and current_event:
            events.append(current_event)
            current_event = {}
    
    class DummyEvent:
        def __init__(self, d):
            self.id = d.get("id")
            self.event = d.get("event")
            self.data = d.get("data")
    
    return [DummyEvent(e) for e in events if "id" in e]

def test_stream_replays_after_last_event_id(client: TestClient) -> None:
    mock_events = [
        StreamEvent(
            id=THIRD_EVENT_ID,
            aggregate_id=ANALYSIS_ID,
            event_type="analysis.stage.started",
            schema_version="1.0",
            sequence=3,
            occurred_at=datetime.now(timezone.utc),
            payload={}
        ),
        StreamEvent(
            id=FOURTH_EVENT_ID,
            aggregate_id=ANALYSIS_ID,
            event_type="analysis.completed",
            schema_version="1.0",
            sequence=4,
            occurred_at=datetime.now(timezone.utc),
            payload={}
        )
    ]
    with patch("citetrace_api.routes.analyses.EventStore") as mock_store_class:
        mock_store = AsyncMock()
        mock_store.after.return_value = mock_events
        mock_store_class.return_value = mock_store
        
        # We need to setup an analysis in the InMemoryAnalysisStore
        command = {
            "workspace_id": WORKSPACE_ID,
            "document_id": str(uuid4()),
            "mode": "understand",
            "scope": {"kind": "whole_document"},
            "audience": "beginner",
            "source_policy_profile": "lawful-open-or-user-upload",
        }
        create_resp = client.post(
            "/v1/analyses",
            headers={"Idempotency-Key": "setup-analysis"},
            json=command,
        )
        assert create_resp.status_code == 202
        created_id = create_resp.json()["id"]

        response = client.get(
            f"/v1/analyses/{created_id}/stream",
            headers={**auth_headers(WORKSPACE_ID), "Last-Event-ID": SECOND_EVENT_ID},
        )
        
        events = parse_sse(response.text)
        assert [event.id for event in events] == [THIRD_EVENT_ID, FOURTH_EVENT_ID]

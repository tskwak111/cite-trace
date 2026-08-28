from uuid import uuid4

import pytest

from citetrace_api.orchestration.evidence_handlers import (
    AnalysisReferencesReadyHandler,
    EvidencePipeline,
)


class MockOutbox:
    def __init__(self):
        self.events = []
    
    def add_event(self, event_type, aggregate_id, workspace_id, payload):
        self.events.append({
            "event_type": event_type,
            "aggregate_id": aggregate_id,
            "workspace_id": workspace_id,
            "payload": payload
        })

@pytest.mark.anyio
async def test_evidence_pipeline_runs():
    outbox = MockOutbox()
    pipeline = EvidencePipeline(outbox_repo=outbox)
    handler = AnalysisReferencesReadyHandler(evidence_pipeline=pipeline)
    
    analysis_id = uuid4()
    workspace_id = uuid4()
    event = {
        "payload": {
            "analysis_id": str(analysis_id),
            "workspace_id": str(workspace_id),
            "total_references": 5
        }
    }
    
    await handler(event)
    
    # We should have outbox event "analysis.completed_with_limits"
    assert len(outbox.events) == 1
    out_event = outbox.events[0]
    assert out_event["event_type"] == "analysis.completed_with_limits"
    assert out_event["aggregate_id"] == analysis_id
    assert out_event["payload"]["status"] == "completed_with_limits"
    assert out_event["payload"]["evidence_link_count"] == 2
    assert out_event["payload"]["limitation_count"] == 3

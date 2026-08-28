from uuid import uuid4

import pytest

from citetrace_api.acquisition.policy import AccessLevel
from citetrace_api.acquisition.service import AcquisitionOutcome
from citetrace_api.orchestration.reference_handlers import (
    DocumentParsedHandler,
    ReferencePipeline,
)
from citetrace_api.providers.models import ProviderCandidate
from citetrace_api.resolution.decision import ResolutionDecision


class MockResolutionService:
    def __init__(self, decisions):
        self.decisions = decisions
        self.calls = []

    async def resolve(self, query, trace_id=""):
        self.calls.append(query)
        return self.decisions.pop(0)

class MockAcquisitionService:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.calls = []

    async def acquire(self, **kwargs):
        self.calls.append(kwargs)
        return self.outcomes.pop(0)

class MockParsedDocsRepo:
    def __init__(self, refs):
        self.refs = refs

    async def get_reference_entries(self, parsed_document_id):
        return self.refs

class MockOutboxRepo:
    def __init__(self):
        self.events = []

    async def add(self, event):
        self.events.append(event)
        
    def add_event(self, event_type, aggregate_id, workspace_id, payload):
        self.events.append({
            "event_type": event_type,
            "aggregate_id": aggregate_id,
            "workspace_id": workspace_id,
            "payload": payload
        })

@pytest.mark.anyio
async def test_reference_pipeline_and_handler():
    workspace_id = uuid4()
    parsed_document_id = uuid4()
    ref1_id = uuid4()
    ref2_id = uuid4()
    ref3_id = uuid4()

    refs = [
        {"id": str(ref1_id), "title": "Resolved OA", "raw_reference": "OA text"},
        {"id": str(ref2_id), "title": "Resolved Abstract", "raw_reference": "Abs text"},
        {"id": str(ref3_id), "title": "Ambiguous", "raw_reference": "Amb text"},
    ]
    
    cand1 = ProviderCandidate(
        provider="unpaywall",
        provider_record_id="oa1",
        title="Resolved OA",
        normalized_title="resolved oa",
        authors=(),
        year=2020,
        venue=None,
        identifiers={"doi": "10.123/oa"},
        version_hints={},
        access_hints={},
        raw_snapshot={}
    )
    
    cand2 = ProviderCandidate(
        provider="unpaywall",
        provider_record_id="abs1",
        title="Resolved Abstract",
        normalized_title="resolved abstract",
        authors=(),
        year=2021,
        venue=None,
        identifiers={"doi": "10.123/abs"},
        version_hints={},
        access_hints={},
        raw_snapshot={"abstract": "Some abstract text"}
    )
    
    cand3_1 = ProviderCandidate(
        provider="crossref",
        provider_record_id="amb1",
        title="Ambiguous",
        normalized_title="ambiguous",
        authors=(),
        year=2022,
        venue=None,
        identifiers={},
        version_hints={},
        access_hints={},
        raw_snapshot={}
    )
    
    cand3_2 = ProviderCandidate(
        provider="openalex",
        provider_record_id="amb2",
        title="Ambiguous",
        normalized_title="ambiguous",
        authors=(),
        year=2022,
        venue=None,
        identifiers={},
        version_hints={},
        access_hints={},
        raw_snapshot={}
    )

    decisions = [
        (ResolutionDecision(status="resolved", selected_candidate_id=f"{cand1.provider}:{cand1.provider_record_id}", selected_work_version_id=None, absolute_score=0.95, score_margin=0.2, reason_codes=(), requires_human_review=False), [cand1]),
        (ResolutionDecision(status="resolved", selected_candidate_id=f"{cand2.provider}:{cand2.provider_record_id}", selected_work_version_id=None, absolute_score=0.92, score_margin=0.1, reason_codes=(), requires_human_review=False), [cand2]),
        (ResolutionDecision(status="ambiguous", selected_candidate_id=None, selected_work_version_id=None, absolute_score=0.85, score_margin=0.01, reason_codes=("multiple_matches",), requires_human_review=True), [cand3_1, cand3_2]),
    ]
    
    outcomes = [
        AcquisitionOutcome(source_asset_id=uuid4(), access_level=AccessLevel.open_access_full_text, acquisition_method="unpaywall_oa", sha256="abc", byte_size=100, limitations=[]),
        AcquisitionOutcome(source_asset_id=uuid4(), access_level=AccessLevel.abstract_only, acquisition_method="abstract_fallback", sha256="def", byte_size=50, limitations=["Full text unavailable"])
    ]

    res_service = MockResolutionService(decisions)
    acq_service = MockAcquisitionService(outcomes)
    pipeline = ReferencePipeline(res_service, acq_service)
    
    parsed_docs_repo = MockParsedDocsRepo(refs)
    outbox_repo = MockOutboxRepo()
    
    handler = DocumentParsedHandler(parsed_docs_repo, pipeline, outbox_repo)
    
    event = {
        "event_type": "document.parsed",
        "aggregate_id": str(parsed_document_id),
        "workspace_id": str(workspace_id),
        "trace_id": "test-trace",
        "payload": {
            "parsed_document_id": str(parsed_document_id),
            "parser_version": "v1",
            "quality_grade": "a"
        }
    }
    
    await handler(event)
    
    assert len(outbox_repo.events) == 1
    outbox_event = outbox_repo.events[0]
    
    # Wait, did we emit "analysis.references.ready" or "document.references.resolved"?
    # The event should be "document.references.resolved" based on my earlier choice
    # Let's support whatever we put in reference_handlers.py
    is_dict = isinstance(outbox_event, dict)
    ev_type = outbox_event["event_type"] if is_dict else outbox_event.event_type
    payload = outbox_event["payload"] if is_dict else outbox_event.payload
    
    assert ev_type == "document.references.resolved"
    assert "reference_pipeline_result" in payload
    
    res = payload["reference_pipeline_result"]
    assert res["total_references"] == 3
    assert res["resolved"] == 2
    assert res["ambiguous"] == 1
    assert res["full_text_available"] == 1
    assert res["abstract_only"] == 1
    
    lims = res["limitations"]
    assert len(lims) == 2 # 1 ambiguous, 1 abstract_only
    
    amb_lim = next(lim for lim in lims if lim["code"] == "reference_ambiguous")
    assert amb_lim["reference_entry_id"] == str(ref3_id)
    assert "user_resolution_required" in amb_lim["recoverable_actions"]
    
    abs_lim = next(lim for lim in lims if lim["code"] == "source_abstract_only")
    assert abs_lim["reference_entry_id"] == str(ref2_id)
    assert "upload_full_text" in abs_lim["recoverable_actions"]


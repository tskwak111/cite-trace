from uuid import uuid4

from citetrace_api.orchestration.outbox import InMemoryOutbox


def test_inmemory_outbox_stores_and_retrieves_events() -> None:
    outbox = InMemoryOutbox()
    aggregate_id = uuid4()
    workspace_id = uuid4()

    event_id = outbox.add_event(
        event_type="document.source.registered",
        aggregate_id=aggregate_id,
        workspace_id=workspace_id,
        payload={"source_asset_id": str(aggregate_id)},
    )

    events = outbox.events_for_aggregate(aggregate_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "document.source.registered"
    assert events[0]["id"] == event_id


def test_inmemory_outbox_filters_by_aggregate() -> None:
    outbox = InMemoryOutbox()
    id1, id2 = uuid4(), uuid4()
    workspace_id = uuid4()

    outbox.add_event("document.source.registered", id1, workspace_id, {"x": "1"})
    outbox.add_event("document.source.registered", id2, workspace_id, {"x": "2"})

    events = outbox.events_for_aggregate(id1)
    assert len(events) == 1

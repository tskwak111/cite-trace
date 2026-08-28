import uuid
from datetime import datetime

from ..db.repositories.feedback import FeedbackRepository
from .models import AdjudicationItem, FeedbackRecord, FeedbackSubmission


class FeedbackService:
    def __init__(self, repository: FeedbackRepository):
        self.repository = repository

    async def submit_feedback(self, submission: FeedbackSubmission) -> FeedbackRecord:
        record = FeedbackRecord(
            id=uuid.uuid4(),
            workspace_id=submission.workspace_id,
            actor_user_id=submission.actor_user_id,
            evidence_link_id=submission.evidence_link_id,
            category=submission.category,
            proposed_relation=submission.proposed_relation,
            proposed_source_span=submission.proposed_source_span,
            comment=submission.comment,
            created_at=datetime.utcnow(),
            idempotency_key=submission.idempotency_key
        )
        await self.repository.append_feedback(record)

        # Simple priority logic
        score = 50.0
        if submission.category in ["source_evidence", "reference_resolution"]:
            score = 90.0

        adj_item = AdjudicationItem(
            id=uuid.uuid4(),
            priority_score=score,
            evidence_link_id=submission.evidence_link_id,
            category=submission.category,
            reported_issue_count=1,
            created_at=datetime.utcnow()
        )
        await self.repository.add_adjudication(adj_item)
        return record

    async def get_adjudication_queue(self) -> list[AdjudicationItem]:
        return await self.repository.get_adjudication_queue()

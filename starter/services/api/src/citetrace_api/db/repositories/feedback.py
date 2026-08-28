
from ...feedback.models import AdjudicationItem, FeedbackRecord


class FeedbackRepository:
    def __init__(self) -> None:
        self._feedbacks: list[FeedbackRecord] = []
        self._adjudications: list[AdjudicationItem] = []

    async def append_feedback(self, feedback: FeedbackRecord) -> None:
        self._feedbacks.append(feedback)

    async def add_adjudication(self, item: AdjudicationItem) -> None:
        self._adjudications.append(item)

    async def get_adjudication_queue(self) -> list[AdjudicationItem]:
        return sorted(self._adjudications, key=lambda x: x.priority_score, reverse=True)

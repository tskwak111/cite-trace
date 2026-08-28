from citetrace_api.domain.models import ProblemDetails


class ProblemException(Exception):
    def __init__(self, problem: ProblemDetails) -> None:
        super().__init__(problem.detail)
        self.problem = problem

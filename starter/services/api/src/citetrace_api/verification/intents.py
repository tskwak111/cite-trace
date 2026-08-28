from enum import Enum


class CitationIntent(Enum):
    background = "background"
    definition = "definition"
    problem_framing = "problem_framing"
    method_adoption = "method_adoption"
    method_extension = "method_extension"
    dataset_use = "dataset_use"
    metric_use = "metric_use"
    benchmark_comparison = "benchmark_comparison"
    result_support = "result_support"
    result_contrast = "result_contrast"
    limitation = "limitation"
    future_direction = "future_direction"
    tool_or_software_use = "tool_or_software_use"
    perfunctory_mention = "perfunctory_mention"


class CitationIntentClassifier:
    pass

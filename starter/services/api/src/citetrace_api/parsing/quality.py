from dataclasses import dataclass
from typing import Literal


@dataclass
class ParseQualityReport:
    grade: Literal["a", "b", "c", "d"]
    features: dict[str, float]
    coordinate_coverage: float
    limitations: list[str]


def grade_parse_quality(
    total_citations: int,
    linked_citations: int,
    total_elements: int,
    elements_with_coords: int,
    has_meaningful_text: bool,
    has_bibliography: bool,
    has_malformed_hierarchy: bool,
) -> ParseQualityReport:
    limitations = []

    if not has_meaningful_text:
        limitations.append("no_meaningful_text")
    if not has_bibliography:
        limitations.append("no_bibliography")
    if has_malformed_hierarchy:
        limitations.append("malformed_hierarchy")

    linkage = linked_citations / total_citations if total_citations > 0 else 1.0
    coord_cov = elements_with_coords / total_elements if total_elements > 0 else 1.0

    features = {"linkage": linkage, "coordinate_coverage": coord_cov}

    if not has_meaningful_text or not has_bibliography or has_malformed_hierarchy:
        return ParseQualityReport("d", features, coord_cov, limitations)

    if linkage >= 0.98 and coord_cov >= 0.90:
        return ParseQualityReport("a", features, coord_cov, limitations)

    if linkage >= 0.90 and coord_cov >= 0.70:
        return ParseQualityReport("b", features, coord_cov, limitations)

    limitations.append("material_linkage_or_coordinate_limitations")
    return ParseQualityReport("c", features, coord_cov, limitations)

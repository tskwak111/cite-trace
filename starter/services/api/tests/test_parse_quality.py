from citetrace_api.parsing.quality import grade_parse_quality


def test_grade_a():
    report = grade_parse_quality(
        total_citations=100, linked_citations=99,
        total_elements=100, elements_with_coords=95,
        has_meaningful_text=True, has_bibliography=True, has_malformed_hierarchy=False
    )
    assert report.grade == "a"

def test_grade_b():
    report = grade_parse_quality(
        total_citations=100, linked_citations=95,
        total_elements=100, elements_with_coords=80,
        has_meaningful_text=True, has_bibliography=True, has_malformed_hierarchy=False
    )
    assert report.grade == "b"

def test_grade_c():
    report = grade_parse_quality(
        total_citations=100, linked_citations=80,
        total_elements=100, elements_with_coords=50,
        has_meaningful_text=True, has_bibliography=True, has_malformed_hierarchy=False
    )
    assert report.grade == "c"
    assert "material_linkage_or_coordinate_limitations" in report.limitations

def test_grade_d_no_text():
    report = grade_parse_quality(
        total_citations=100, linked_citations=100,
        total_elements=100, elements_with_coords=100,
        has_meaningful_text=False, has_bibliography=True, has_malformed_hierarchy=False
    )
    assert report.grade == "d"
    assert "no_meaningful_text" in report.limitations

def test_grade_d_malformed():
    report = grade_parse_quality(
        total_citations=100, linked_citations=100,
        total_elements=100, elements_with_coords=100,
        has_meaningful_text=True, has_bibliography=True, has_malformed_hierarchy=True
    )
    assert report.grade == "d"
    assert "malformed_hierarchy" in report.limitations

from pathlib import Path

import pytest

from citetrace_api.parsing.tei_reader import TeiReader


@pytest.fixture
def tei_xml():
    path = Path(__file__).parent / "fixtures" / "grobid-fulltext.tei.xml"
    return path.read_bytes()

def test_extract_references(tei_xml):
    reader = TeiReader(tei_xml)
    refs = reader.extract_references()
    assert len(refs) == 1
    ref = refs[0]
    assert ref.xml_id == "b12"
    assert ref.title == "Cited Paper Title"
    assert "John Smith" in ref.authors
    assert ref.year == "2020"
    assert ref.venue == "Journal of Testing"
    assert ref.identifiers.get("DOI") == "10.1234/test.123"
    assert ref.coordinates == "1,150.0,150.0,300.0,20.0"

def test_extract_citation_clusters(tei_xml):
    reader = TeiReader(tei_xml)
    clusters = reader.extract_citation_clusters()
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster.anchor_text == "[12]"
    assert cluster.target_reference_xml_ids == ["b12"]
    assert cluster.coordinates == "1,100.0,100.0,50.0,20.0"

def test_extract_structural_nodes(tei_xml):
    reader = TeiReader(tei_xml)
    nodes = reader.extract_structural_nodes()
    assert len(nodes) == 1
    node = nodes[0]
    assert node.xml_id == "sec1"
    assert node.head == "Introduction"
    assert "This is some text" in node.text

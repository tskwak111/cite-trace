from citetrace_api.parsing.normalizer import DocumentNormalizer
from citetrace_api.parsing.tei_reader import TeiCitationCluster


def test_normalize_text():
    normalizer = DocumentNormalizer()
    assert normalizer.normalize_text("This \n  is \t a   test.") == "This is a test."


def test_process():
    normalizer = DocumentNormalizer()
    raw_text = "This \n is a \t text with a citation [12] inline."

    cluster = TeiCitationCluster(
        anchor_text="[12]",
        target_reference_xml_ids=["b12"],
        coordinates="1,100,100,50,20",
        context_node_xml_id="sec1",
    )

    doc = normalizer.process(raw_text, [cluster])

    assert doc.normalized_text == "This is a text with a citation [12] inline."
    assert len(doc.offset_mappings) == 1
    mapping = doc.offset_mappings[0]

    assert mapping.normalized_start == 31
    assert mapping.normalized_end == 35
    assert mapping.tei_node_id == "sec1"
    assert mapping.page == "1"
    assert mapping.bounding_boxes == "1,100,100,50,20"

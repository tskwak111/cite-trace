from dataclasses import dataclass

from lxml import etree
from typing import Any, cast

NS = {"tei": "http://www.tei-c.org/ns/1.0"}

@dataclass
class TeiReference:
    xml_id: str
    local_label: str
    raw_reference: str
    title: str | None
    authors: list[str]
    year: str | None
    venue: str | None
    identifiers: dict[str, str]
    coordinates: str | None

@dataclass
class TeiCitationCluster:
    anchor_text: str
    target_reference_xml_ids: list[str]
    coordinates: str | None
    context_node_xml_id: str | None

@dataclass
class ParsedStructuralNode:
    xml_id: str | None
    tag: str
    text: str
    head: str | None

class TeiReader:
    def __init__(self, xml_bytes: bytes):
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        self.root = cast(Any, etree.fromstring(xml_bytes, parser=parser))
        
    def extract_references(self) -> list[TeiReference]:
        refs = []
        for bibl in self.root.xpath(".//tei:listBibl/tei:biblStruct", namespaces=NS):
            xml_id = bibl.get("{http://www.w3.org/XML/1998/namespace}id")
            if not xml_id:
                xml_id = bibl.get("xml:id") # Fallback
                
            coords = bibl.get("coords")
            
            title = None
            title_node = bibl.xpath(".//tei:title[@level='a']", namespaces=NS)
            if title_node:
                title = "".join(title_node[0].itertext()).strip()
                
            authors = []
            for author_node in bibl.xpath(".//tei:author/tei:persName", namespaces=NS):
                name_parts = [t.strip() for t in author_node.itertext() if t.strip()]
                if name_parts:
                    authors.append(" ".join(name_parts))
            
            year = None
            date_node = bibl.xpath(".//tei:date[@type='published']", namespaces=NS)
            if date_node:
                year = date_node[0].get("when")
                
            venue = None
            venue_node = bibl.xpath(".//tei:title[@level='j']", namespaces=NS)
            if venue_node:
                venue = "".join(venue_node[0].itertext()).strip()
                
            identifiers = {}
            for idno in bibl.xpath(".//tei:idno", namespaces=NS):
                id_type = idno.get("type")
                if id_type:
                    identifiers[id_type] = "".join(idno.itertext()).strip()
                    
            raw_reference = "".join(bibl.itertext()).strip()
            
            refs.append(TeiReference(
                xml_id=xml_id or "",
                local_label=f"[{xml_id}]", # Simplification
                raw_reference=raw_reference,
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                identifiers=identifiers,
                coordinates=coords
            ))
        return refs

    def extract_citation_clusters(self) -> list[TeiCitationCluster]:
        clusters = []
        for ref in self.root.xpath(".//tei:body//tei:ref[@type='bibr']", namespaces=NS):
            target = ref.get("target")
            coords = ref.get("coords")
            anchor_text = "".join(ref.itertext()).strip()
            
            parent = ref.getparent()
            parent_id = parent.get("{http://www.w3.org/XML/1998/namespace}id") if parent is not None else None
            
            targets = []
            if target:
                targets = [t.lstrip("#") for t in target.split()]
                
            clusters.append(TeiCitationCluster(
                anchor_text=anchor_text,
                target_reference_xml_ids=targets,
                coordinates=coords,
                context_node_xml_id=parent_id
            ))
        return clusters

    def extract_structural_nodes(self) -> list[ParsedStructuralNode]:
        nodes = []
        for div in self.root.xpath(".//tei:body/tei:div", namespaces=NS):
            xml_id = div.get("{http://www.w3.org/XML/1998/namespace}id")
            head = None
            head_node = div.xpath("./tei:head", namespaces=NS)
            if head_node:
                head = "".join(head_node[0].itertext()).strip()
                
            text = "".join(div.itertext()).strip()
            
            nodes.append(ParsedStructuralNode(
                xml_id=xml_id,
                tag="div",
                text=text,
                head=head
            ))
        return nodes

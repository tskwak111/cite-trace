from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ParsedDocumentsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def save_parsed_document(self, doc_data: dict[str, Any]) -> str:
        # Simplified schema definition for the repository
        query = text("""
            INSERT INTO parsed_documents 
            (id, source_asset_id, tei_xml_sha256, normalized_text, text_sha256, quality_grade, created_at)
            VALUES (:id, :source_asset_id, :tei_xml_sha256, :normalized_text, :text_sha256, :quality_grade, :created_at)
            RETURNING id
        """)
        result = await self.session.execute(query, doc_data)
        return str(result.scalar_one())
        
    async def save_parsed_nodes(self, nodes_data: list[dict[str, Any]]) -> None:
        if not nodes_data:
            return
        query = text("""
            INSERT INTO parsed_nodes (id, parsed_document_id, xml_id, tag, head, text_content)
            VALUES (:id, :parsed_document_id, :xml_id, :tag, :head, :text_content)
        """)
        await self.session.execute(query, nodes_data)
        
    async def save_reference_entries(self, refs_data: list[dict[str, Any]]) -> None:
        if not refs_data:
            return
        query = text("""
            INSERT INTO reference_entries 
            (id, parsed_document_id, xml_id, local_label, raw_reference, title, year, venue, identifiers, coordinates)
            VALUES (:id, :parsed_document_id, :xml_id, :local_label, :raw_reference, :title, :year, :venue, :identifiers, :coordinates)
        """)
        await self.session.execute(query, refs_data)

    async def save_citation_clusters(self, clusters_data: list[dict[str, Any]]) -> None:
        if not clusters_data:
            return
        query = text("""
            INSERT INTO citation_clusters
            (id, parsed_document_id, context_node_id, anchor_text, coordinates)
            VALUES (:id, :parsed_document_id, :context_node_id, :anchor_text, :coordinates)
        """)
        await self.session.execute(query, clusters_data)
        
    async def save_citation_anchors(self, anchors_data: list[dict[str, Any]]) -> None:
        if not anchors_data:
            return
        query = text("""
            INSERT INTO citation_anchors
            (id, cluster_id, reference_entry_id)
            VALUES (:id, :cluster_id, :reference_entry_id)
        """)
        await self.session.execute(query, anchors_data)

    async def get_reference_entries(self, parsed_document_id: str) -> list[dict[str, Any]]:
        query = text("""
            SELECT id, xml_id, local_label, raw_reference, title, year, venue, identifiers, coordinates 
            FROM reference_entries 
            WHERE parsed_document_id = :parsed_document_id
        """)
        result = await self.session.execute(query, {"parsed_document_id": parsed_document_id})
        return [dict(row._mapping) for row in result.fetchall()]

"""
CyberGhost OSINT Enterprise — Qdrant RAG Service
Vector database for threat intelligence knowledge base
"""
from __future__ import annotations

import hashlib
from typing import Any

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from backend.core.config import settings

log = structlog.get_logger(__name__)

COLLECTION = settings.qdrant.collection
VECTOR_SIZE = 768  # nomic-embed-text dimension


class QdrantRAG:
    """
    Qdrant-based RAG service for threat intelligence knowledge base.
    Stores and retrieves OSINT reports, IOC context, and threat intelligence.
    """

    def __init__(self) -> None:
        api_key = settings.qdrant.api_key
        self.client = AsyncQdrantClient(
            url=settings.qdrant.url,
            api_key=api_key.get_secret_value() if api_key else None,
        )

    async def initialize_collection(self) -> None:
        """Create the collection if it doesn't exist."""
        try:
            await self.client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            log.info("qdrant_collection_created", collection=COLLECTION)
        except Exception as e:
            if "already exists" in str(e).lower():
                log.debug("qdrant_collection_exists", collection=COLLECTION)
            else:
                log.error("qdrant_collection_error", error=str(e))
                raise

    async def embed_text(self, text: str) -> list[float]:
        """Generate embeddings using configured model."""
        try:
            # Try Ollama embeddings first (local, private)
            from langchain_community.embeddings import OllamaEmbeddings
            embedder = OllamaEmbeddings(
                base_url=settings.ai.ollama_base_url,
                model=settings.ai.embedding_model,
            )
            return await embedder.aembed_query(text)
        except Exception:
            # Fallback: sentence-transformers (local)
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            return model.encode(text).tolist()

    async def add_document(
        self,
        content: str,
        metadata: dict[str, Any],
        doc_type: str = "threat_report",
    ) -> str:
        """
        Add a document to the knowledge base.
        Returns the document ID.
        """
        # Generate stable ID from content hash
        doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        point_id = int(doc_id, 16) % (2**63)  # Qdrant needs integer ID

        vector = await self.embed_text(content)

        point = PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "content": content,
                "doc_type": doc_type,
                "metadata": metadata,
            },
        )

        await self.client.upsert(
            collection_name=COLLECTION,
            points=[point],
        )

        log.info("document_added", doc_type=doc_type, doc_id=doc_id)
        return doc_id

    async def similarity_search(
        self,
        query: str,
        limit: int = 5,
        doc_type: str | None = None,
        score_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents using semantic similarity.
        Returns documents sorted by relevance.
        """
        vector = await self.embed_text(query)

        search_filter = None
        if doc_type:
            search_filter = Filter(
                must=[FieldCondition(key="doc_type", match=MatchValue(value=doc_type))]
            )

        results = await self.client.search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=limit,
            query_filter=search_filter,
            score_threshold=score_threshold,
            with_payload=True,
        )

        return [
            {
                "score": result.score,
                "content": result.payload.get("content", ""),
                "metadata": result.payload.get("metadata", {}),
                "doc_type": result.payload.get("doc_type"),
            }
            for result in results
        ]

    async def add_ioc_context(
        self, ioc_value: str, ioc_type: str, enrichment_data: dict[str, Any]
    ) -> str:
        """Add IOC enrichment data to the knowledge base."""
        # Create a natural language description for embedding
        content = self._ioc_to_text(ioc_value, ioc_type, enrichment_data)
        metadata = {
            "ioc_value": ioc_value,
            "ioc_type": ioc_type,
            "malicious": enrichment_data.get("malicious", False),
            "reputation_score": enrichment_data.get("reputation", {}).get("score", 0),
        }
        return await self.add_document(content, metadata, doc_type="ioc_enrichment")

    async def add_threat_report(
        self, title: str, content: str, source: str, tags: list[str] | None = None
    ) -> str:
        """Add a threat intelligence report to the knowledge base."""
        metadata = {"title": title, "source": source, "tags": tags or []}
        return await self.add_document(content, metadata, doc_type="threat_report")

    def _ioc_to_text(
        self, value: str, ioc_type: str, data: dict[str, Any]
    ) -> str:
        """Convert IOC data to natural language for embedding."""
        parts = [f"IOC: {value} (type: {ioc_type})"]

        reputation = data.get("reputation", {})
        if reputation:
            parts.append(
                f"Reputation score: {reputation.get('score', 0)}/100, "
                f"Risk level: {reputation.get('risk_level', 'unknown')}"
            )

        vt = data.get("virustotal", {})
        if vt.get("found"):
            parts.append(
                f"VirusTotal: {vt.get('malicious', 0)} malicious detections "
                f"out of {vt.get('total', 0)} engines"
            )

        gn = data.get("greynoise", {})
        if gn.get("found"):
            parts.append(f"GreyNoise classification: {gn.get('classification', 'unknown')}")

        shodan = data.get("shodan", {})
        if shodan.get("found"):
            vulns = shodan.get("vulnerabilities", [])
            if vulns:
                parts.append(f"Known vulnerabilities: {', '.join(vulns[:5])}")
            ports = shodan.get("ports", [])
            if ports:
                parts.append(f"Open ports: {', '.join(map(str, ports[:10]))}")

        otx = data.get("alienvault", {})
        if otx.get("pulse_count", 0) > 0:
            parts.append(f"AlienVault OTX pulses: {otx.get('pulse_count')}")

        return ". ".join(parts)

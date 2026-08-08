"""
CyberGhost OSINT Enterprise — Attack Graph Engine (V15.0)
Neo4j Graph Database Models for Attack Surface Management & CTI Correlation
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from neo4j import AsyncGraphDatabase, AsyncDriver

from backend.core.config import settings

log = structlog.get_logger(__name__)

# ── Security: Allowlist for relationship types (prevents Cypher Injection) ────
ALLOWED_RELATIONSHIP_TYPES: frozenset[str] = frozenset({
    # Attack Graph Relationships
    "HOSTED_ON",
    "OWNS",
    "EXPOSES",
    "CONNECTS_TO",
    "AFFECTS",
    "RELATED_TO",
    "PART_OF",
    "RESOLVES_TO",
    
    # CTI Relationships
    "ATTRIBUTED_TO",
    "USES",
    "TARGETS",
    "COMMUNICATES_WITH",
    "DELIVERED_BY",
    "EXPLOITS",
    "MITIGATES",
    "CONDUCTS",
    "OBSERVED_IN",
    "DROPS",
    "DOWNLOADS",
})

# Allowed Labels for nodes to prevent injection in dynamic queries
ALLOWED_LABELS: frozenset[str] = frozenset({
    "Domain", "Subdomain", "IP", "ASN", "Certificate", "Email", 
    "Employee", "Breach", "Technology", "Vulnerability", 
    "IOC", "ThreatActor", "Campaign", "Malware"
})


class KnowledgeGraph:
    """
    Neo4j-based Attack Graph Engine for Attack Surface Modeling and CTI.
    """

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j.uri,
            auth=(
                settings.neo4j.username,
                settings.neo4j.password.get_secret_value(),
            ),
        )
        await self._setup_constraints()
        log.info("neo4j_attack_graph_connected")

    async def disconnect(self) -> None:
        if self._driver:
            await self._driver.close()
            log.info("neo4j_attack_graph_disconnected")

    async def _setup_constraints(self) -> None:
        constraints = [
            "CREATE CONSTRAINT domain_value IF NOT EXISTS FOR (n:Domain) REQUIRE n.value IS UNIQUE",
            "CREATE CONSTRAINT ip_value IF NOT EXISTS FOR (n:IP) REQUIRE n.value IS UNIQUE",
            "CREATE CONSTRAINT vuln_cve IF NOT EXISTS FOR (n:Vulnerability) REQUIRE n.cve_id IS UNIQUE",
            "CREATE CONSTRAINT ioc_value IF NOT EXISTS FOR (n:IOC) REQUIRE n.value IS UNIQUE",
            "CREATE INDEX domain_tenant IF NOT EXISTS FOR (n:Domain) ON (n.tenant_id)",
        ]
        async with self._driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    log.debug("constraint_skip", error=str(e))

    # ── Attack Surface Nodes ──────────────────────────────────────────────────

    async def upsert_node(
        self,
        label: str,
        value: str,
        tenant_id: str,
        properties: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generic method to upsert any Attack Graph node securely."""
        if label not in ALLOWED_LABELS:
            raise ValueError(f"Invalid Node Label: {label}")
            
        props = properties or {}
        props["tenant_id"] = tenant_id
        
        # We can dynamically set the label because we validated it against the ALLOWLIST
        query = f"""
        MERGE (n:{label} {{value: $value}})
        ON CREATE SET
            n += $props,
            n.first_seen = datetime(),
            n.last_seen = datetime()
        ON MATCH SET
            n += $props,
            n.last_seen = datetime()
        RETURN n
        """
        async with self._driver.session() as session:
            result = await session.run(query, value=value, props=props)
            record = await result.single()
            return dict(record["n"]) if record else {}

    # ── Attack Surface Relationships ──────────────────────────────────────────

    async def link_nodes(
        self, 
        source_label: str, source_value: str, 
        target_label: str, target_value: str, 
        relationship_type: str, 
        properties: dict[str, Any] | None = None
    ) -> bool:
        """Create a relationship between two nodes securely."""
        
        if relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
            raise ValueError(f"Invalid relationship type '{relationship_type}'")
        if source_label not in ALLOWED_LABELS or target_label not in ALLOWED_LABELS:
            raise ValueError("Invalid source or target label")

        query = f"""
        MATCH (a:{source_label} {{value: $source}})
        MATCH (b:{target_label} {{value: $target}})
        MERGE (a)-[r:{relationship_type}]->(b)
        ON CREATE SET r += $props, r.created = datetime()
        ON MATCH SET r += $props, r.last_seen = datetime()
        RETURN r
        """
        async with self._driver.session() as session:
            result = await session.run(query, source=source_value, target=target_value, props=properties or {})
            return await result.single() is not None

    # ── Cypher Queries (Attack Graph Intelligence) ────────────────────────────

    async def find_critical_attack_paths(self, tenant_id: str) -> list[dict]:
        """
        Descobre caminhos críticos: IP Exposto com Vulnerabilidade crítica que hospeda um Domínio do Tenant.
        """
        query = """
        MATCH path = (d:Domain {tenant_id: $tenant_id})-[:HOSTED_ON|RESOLVES_TO]->(ip:IP)-[:AFFECTS]-(v:Vulnerability {severity: 'critical'})
        RETURN nodes(path) AS nodes, relationships(path) AS rels
        LIMIT 50
        """
        async with self._driver.session() as session:
            result = await session.run(query, tenant_id=tenant_id)
            records = await result.data()
            return records

    async def find_indirect_exposure(self, tenant_id: str) -> list[dict]:
        """
        Exposição Indireta: Domínios conectados a IPs que compartilham infraestrutura com domínios maliciosos.
        """
        query = """
        MATCH (d1:Domain {tenant_id: $tenant_id})-[:HOSTED_ON]->(ip:IP)<-[:HOSTED_ON]-(d2:Domain)
        MATCH (d2)-[:RELATED_TO]->(c:Campaign)
        RETURN d1.value AS target, ip.value AS shared_ip, d2.value AS malicious_neighbor, c.name AS campaign
        """
        async with self._driver.session() as session:
            result = await session.run(query, tenant_id=tenant_id)
            return await result.data()


# Global instance
knowledge_graph = KnowledgeGraph()

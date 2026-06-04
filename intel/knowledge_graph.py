"""
CyberGhost OSINT Enterprise — Neo4j Knowledge Graph
IOC correlation, threat actor profiling, campaign tracking
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from neo4j import AsyncGraphDatabase, AsyncDriver

from backend.core.config import settings

log = structlog.get_logger(__name__)

# ── Security: Allowlist for relationship types (prevents Cypher Injection) ────
# NEVER interpolate user-provided strings into Cypher queries.
# This allowlist validates relationship_type before it enters any f-string.
ALLOWED_RELATIONSHIP_TYPES: frozenset[str] = frozenset({
    "RELATED_TO",
    "ATTRIBUTED_TO",
    "USES",
    "TARGETS",
    "PART_OF",
    "COMMUNICATES_WITH",
    "HOSTED_ON",
    "DELIVERED_BY",
    "EXPLOITS",
    "MITIGATES",
    "CONDUCTS",
    "OBSERVED_IN",
    "DROPS",
    "DOWNLOADS",
})



class KnowledgeGraph:
    """
    Neo4j-based Knowledge Graph for threat intelligence correlation.

    Node types:
        IOC, ThreatActor, Campaign, Malware, Infrastructure, Victim,
        AttackPattern, Vulnerability, Organization, Domain, IP, Hash, Email

    Relationship types:
        ATTRIBUTED_TO, USES, TARGETS, PART_OF, COMMUNICATES_WITH,
        RELATED_TO, HOSTED_ON, DELIVERED_BY, EXPLOITS, MITIGATES
    """

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Initialize Neo4j connection."""
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j.uri,
            auth=(
                settings.neo4j.username,
                settings.neo4j.password.get_secret_value(),
            ),
        )
        await self._setup_constraints()
        log.info("neo4j_connected")

    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            await self._driver.close()
            log.info("neo4j_disconnected")

    async def _setup_constraints(self) -> None:
        """Create indexes and constraints on first run."""
        constraints = [
            "CREATE CONSTRAINT ioc_value IF NOT EXISTS FOR (n:IOC) REQUIRE n.value IS UNIQUE",
            "CREATE CONSTRAINT actor_name IF NOT EXISTS FOR (n:ThreatActor) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT campaign_name IF NOT EXISTS FOR (n:Campaign) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT malware_name IF NOT EXISTS FOR (n:Malware) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT vuln_cve IF NOT EXISTS FOR (n:Vulnerability) REQUIRE n.cve_id IS UNIQUE",
            # Indexes for performance
            "CREATE INDEX ioc_type IF NOT EXISTS FOR (n:IOC) ON (n.ioc_type)",
            "CREATE INDEX ioc_malicious IF NOT EXISTS FOR (n:IOC) ON (n.malicious)",
            "CREATE INDEX ioc_score IF NOT EXISTS FOR (n:IOC) ON (n.reputation_score)",
        ]

        async with self._driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    log.debug("constraint_skip", error=str(e))

    # ── IOC Operations ────────────────────────────────────────────────────────

    async def upsert_ioc(
        self,
        value: str,
        ioc_type: str,
        reputation_score: int | None = None,
        malicious: bool = False,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create or update an IOC node in the graph.
        Returns the created/updated node properties.
        """
        query = """
        MERGE (ioc:IOC {value: $value})
        ON CREATE SET
            ioc.ioc_type = $ioc_type,
            ioc.reputation_score = $reputation_score,
            ioc.malicious = $malicious,
            ioc.tags = $tags,
            ioc.first_seen = datetime(),
            ioc.last_seen = datetime(),
            ioc.metadata = $metadata
        ON MATCH SET
            ioc.reputation_score = $reputation_score,
            ioc.malicious = $malicious,
            ioc.last_seen = datetime(),
            ioc.tags = coalesce($tags, ioc.tags)
        RETURN ioc
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                value=value,
                ioc_type=ioc_type,
                reputation_score=reputation_score,
                malicious=malicious,
                tags=tags or [],
                metadata=str(metadata or {}),
            )
            record = await result.single()
            return dict(record["ioc"]) if record else {}

    async def link_iocs(
        self, source_value: str, target_value: str, relationship_type: str = "RELATED_TO"
    ) -> bool:
        """Create a relationship between two IOC nodes.

        Security: relationship_type is validated against ALLOWED_RELATIONSHIP_TYPES
        before interpolation into Cypher — prevents Cypher Injection.
        Never pass user-provided strings directly as relationship_type.
        """
        # SECURITY: Validate against allowlist BEFORE any string interpolation
        if relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
            log.warning(
                "cypher_injection_attempt_blocked",
                relationship_type=relationship_type,
                allowed=list(ALLOWED_RELATIONSHIP_TYPES),
            )
            raise ValueError(
                f"Invalid relationship type '{relationship_type}'. "
                f"Must be one of: {sorted(ALLOWED_RELATIONSHIP_TYPES)}"
            )

        # Safe to interpolate: relationship_type is from a validated allowlist,
        # not raw user input. Cypher does not support parameterized relationship types.
        query = f"""
        MATCH (a:IOC {{value: $source}})
        MATCH (b:IOC {{value: $target}})
        MERGE (a)-[r:{relationship_type}]->(b)
        ON CREATE SET r.created = datetime(), r.weight = 1
        ON MATCH SET r.weight = r.weight + 1, r.last_seen = datetime()
        RETURN r
        """
        async with self._driver.session() as session:
            result = await session.run(query, source=source_value, target=target_value)
            return await result.single() is not None


    async def get_ioc_neighbors(
        self, value: str, depth: int = 2, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get all IOCs connected to a given IOC up to specified depth.
        Returns graph data for visualization.
        """
        query = """
        MATCH path = (start:IOC {value: $value})-[*1..$depth]-(neighbor)
        WITH nodes(path) AS ns, relationships(path) AS rels
        LIMIT $limit
        RETURN
            [n IN ns | {id: elementId(n), labels: labels(n), properties: properties(n)}] AS nodes,
            [r IN rels | {
                id: elementId(r),
                type: type(r),
                source: elementId(startNode(r)),
                target: elementId(endNode(r)),
                properties: properties(r)
            }] AS relationships
        """
        async with self._driver.session() as session:
            result = await session.run(query, value=value, depth=depth, limit=limit)
            records = await result.data()

            nodes: dict[str, Any] = {}
            relationships: list[dict] = []

            for record in records:
                for node in record["nodes"]:
                    nodes[node["id"]] = node
                for rel in record["relationships"]:
                    relationships.append(rel)

            return {
                "nodes": list(nodes.values()),
                "relationships": relationships,
                "total_nodes": len(nodes),
            }

    # ── Threat Actor Operations ───────────────────────────────────────────────

    async def upsert_threat_actor(
        self,
        name: str,
        aliases: list[str] | None = None,
        country: str | None = None,
        motivation: str | None = None,
        sophistication: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a Threat Actor node."""
        query = """
        MERGE (ta:ThreatActor {name: $name})
        ON CREATE SET
            ta.aliases = $aliases,
            ta.country = $country,
            ta.motivation = $motivation,
            ta.sophistication = $sophistication,
            ta.description = $description,
            ta.created = datetime()
        ON MATCH SET
            ta.last_updated = datetime(),
            ta.aliases = coalesce($aliases, ta.aliases)
        RETURN ta
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                name=name,
                aliases=aliases or [],
                country=country,
                motivation=motivation,
                sophistication=sophistication,
                description=description,
            )
            record = await result.single()
            return dict(record["ta"]) if record else {}

    async def attribute_ioc_to_actor(
        self, ioc_value: str, actor_name: str, confidence: int = 50
    ) -> bool:
        """Link an IOC to a threat actor with confidence score."""
        query = """
        MATCH (ioc:IOC {value: $ioc_value})
        MATCH (ta:ThreatActor {name: $actor_name})
        MERGE (ioc)-[r:ATTRIBUTED_TO]->(ta)
        ON CREATE SET r.confidence = $confidence, r.created = datetime()
        ON MATCH SET r.confidence = $confidence
        RETURN r
        """
        async with self._driver.session() as session:
            result = await session.run(
                query, ioc_value=ioc_value, actor_name=actor_name, confidence=confidence
            )
            return await result.single() is not None

    # ── Campaign Operations ───────────────────────────────────────────────────

    async def upsert_campaign(
        self,
        name: str,
        description: str | None = None,
        first_seen: str | None = None,
        last_seen: str | None = None,
        objective: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a Campaign node."""
        query = """
        MERGE (c:Campaign {name: $name})
        ON CREATE SET
            c.description = $description,
            c.first_seen = $first_seen,
            c.last_seen = $last_seen,
            c.objective = $objective,
            c.created = datetime()
        ON MATCH SET c.last_updated = datetime()
        RETURN c
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                name=name,
                description=description,
                first_seen=first_seen,
                last_seen=last_seen,
                objective=objective,
            )
            record = await result.single()
            return dict(record["c"]) if record else {}

    async def link_actor_to_campaign(
        self, actor_name: str, campaign_name: str
    ) -> bool:
        """Link a threat actor to a campaign."""
        query = """
        MATCH (ta:ThreatActor {name: $actor_name})
        MATCH (c:Campaign {name: $campaign_name})
        MERGE (ta)-[r:CONDUCTS]->(c)
        ON CREATE SET r.created = datetime()
        RETURN r
        """
        async with self._driver.session() as session:
            result = await session.run(
                query, actor_name=actor_name, campaign_name=campaign_name
            )
            return await result.single() is not None

    # ── Analytics Queries ─────────────────────────────────────────────────────

    async def find_related_malicious_iocs(
        self, ioc_value: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Find malicious IOCs related to a given IOC through graph traversal."""
        query = """
        MATCH (start:IOC {value: $value})-[*1..3]-(related:IOC)
        WHERE related.malicious = true AND related.value <> $value
        RETURN related, count(*) AS relevance
        ORDER BY relevance DESC, related.reputation_score DESC
        LIMIT $limit
        """
        async with self._driver.session() as session:
            result = await session.run(query, value=ioc_value, limit=limit)
            records = await result.data()
            return [
                {**dict(r["related"]), "relevance": r["relevance"]}
                for r in records
            ]

    async def get_threat_actor_infrastructure(
        self, actor_name: str
    ) -> dict[str, Any]:
        """Get all infrastructure associated with a threat actor."""
        query = """
        MATCH (ta:ThreatActor {name: $actor_name})
        OPTIONAL MATCH (ioc:IOC)-[:ATTRIBUTED_TO]->(ta)
        OPTIONAL MATCH (ta)-[:CONDUCTS]->(c:Campaign)
        OPTIONAL MATCH (ta)-[:USES]->(m:Malware)
        RETURN
            ta,
            collect(DISTINCT ioc) AS iocs,
            collect(DISTINCT c) AS campaigns,
            collect(DISTINCT m) AS malware
        """
        async with self._driver.session() as session:
            result = await session.run(query, actor_name=actor_name)
            record = await result.single()
            if not record:
                return {}

            return {
                "actor": dict(record["ta"]),
                "iocs": [dict(i) for i in record["iocs"] if i],
                "campaigns": [dict(c) for c in record["campaigns"] if c],
                "malware": [dict(m) for m in record["malware"] if m],
            }

    async def get_graph_statistics(self) -> dict[str, int]:
        """Get overall graph statistics."""
        query = """
        MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count
        ORDER BY count DESC
        """
        async with self._driver.session() as session:
            result = await session.run(query)
            records = await result.data()
            return {r["label"]: r["count"] for r in records if r["label"]}

    async def batch_upsert_iocs(
        self, iocs: list[dict[str, Any]]
    ) -> int:
        """
        Batch upsert IOCs using UNWIND — dramatically faster than individual upserts.
        For 50,000 IOCs: individual = 50,000 transactions, batch = 50-100 transactions.

        Each IOC dict must have: value, ioc_type.
        Optional: reputation_score, malicious, tags, metadata.
        """
        query = """
        UNWIND $iocs AS ioc_data
        MERGE (ioc:IOC {value: ioc_data.value})
        ON CREATE SET
            ioc.ioc_type = ioc_data.ioc_type,
            ioc.reputation_score = ioc_data.reputation_score,
            ioc.malicious = ioc_data.malicious,
            ioc.tags = ioc_data.tags,
            ioc.first_seen = datetime(),
            ioc.last_seen = datetime()
        ON MATCH SET
            ioc.reputation_score = ioc_data.reputation_score,
            ioc.malicious = ioc_data.malicious,
            ioc.last_seen = datetime()
        RETURN count(*) AS total
        """
        # Process in batches of 1000 to avoid OOM in Neo4j
        batch_size = 1000
        total_processed = 0

        for i in range(0, len(iocs), batch_size):
            batch = iocs[i:i + batch_size]
            async with self._driver.session() as session:
                result = await session.run(query, iocs=batch)
                record = await result.single()
                if record:
                    total_processed += record["total"]

        log.info("batch_upsert_completed", total=total_processed)
        return total_processed


# Global instance
knowledge_graph = KnowledgeGraph()

"""
CyberGhost OSINT Enterprise — AI Investigation Agent
LangGraph multi-agent system for autonomous OSINT investigation
"""
from __future__ import annotations

import asyncio
from typing import Any, TypedDict

import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from backend.core.config import settings

log = structlog.get_logger(__name__)


# ── LLM Factory ───────────────────────────────────────────────────────────────


def get_llm(temperature: float = 0.1) -> Any:
    """
    Get LLM based on configuration.
    Falls back gracefully: anthropic → openai → ollama (local)
    """
    provider = settings.ai.provider

    if provider == "anthropic" and settings.ai.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.ai.anthropic_api_key.get_secret_value(),
            temperature=temperature,
        )

    if provider == "openai" and settings.ai.openai_api_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.ai.openai_api_key.get_secret_value(),
            temperature=temperature,
        )

    # Default: Ollama (local, private, no API cost)
    from langchain_community.chat_models import ChatOllama
    return ChatOllama(
        base_url=settings.ai.ollama_base_url,
        model=settings.ai.ollama_model,
        temperature=temperature,
    )


# ── Agent State ───────────────────────────────────────────────────────────────


class InvestigationState(TypedDict):
    """State passed between nodes in the investigation graph."""
    target: str
    investigation_id: str
    messages: list[Any]
    recon_results: dict[str, Any]
    intel_results: dict[str, Any]
    graph_results: dict[str, Any]
    analysis: str
    report: str
    error: str | None
    next_action: str


# ── Tools ─────────────────────────────────────────────────────────────────────


@tool
async def run_recon(target: str) -> dict[str, Any]:
    """
    Run reconnaissance on a target (domain, IP, email, hash).
    Returns DNS, WHOIS, subdomains, and certificate transparency data.
    """
    from recon.cert_transparency import CertificateTransparency
    from recon.asn_intel import ASNIntelligence

    results = {}
    ct = CertificateTransparency()
    asn = ASNIntelligence()

    tasks = await asyncio.gather(
        ct.lookup(target),
        asn.lookup(target),
        return_exceptions=True,
    )

    results["cert_transparency"] = tasks[0] if not isinstance(tasks[0], Exception) else {}
    results["asn"] = tasks[1] if not isinstance(tasks[1], Exception) else {}
    return results


@tool
async def run_threat_intel(target: str) -> dict[str, Any]:
    """
    Run threat intelligence enrichment on a target.
    Queries VirusTotal, AbuseIPDB, GreyNoise, AlienVault OTX, Shodan in parallel.
    Returns reputation score and malicious indicators.
    """
    from intel.threat_intel import ThreatIntelligence
    ti = ThreatIntelligence()
    return await ti.enrich(target)


@tool
async def query_knowledge_graph(query: str) -> dict[str, Any]:
    """
    Query the Neo4j knowledge graph for related IOCs, threat actors, and campaigns.
    Input: an IOC value (IP, domain, hash, etc.)
    """
    from intel.knowledge_graph import knowledge_graph
    return await knowledge_graph.get_ioc_neighbors(query, depth=2, limit=30)


@tool
async def search_rag_knowledge(query: str) -> list[dict[str, Any]]:
    """
    Search the RAG knowledge base for relevant threat intelligence reports and IOC context.
    Returns the most relevant documents and their similarity scores.
    """
    from ai.rag.qdrant_service import QdrantRAG
    rag = QdrantRAG()
    return await rag.similarity_search(query, limit=5)


@tool
async def create_stix_bundle(target: str, ioc_data: dict[str, Any]) -> str:
    """
    Create a STIX 2.1 bundle from collected IOC data.
    Returns a JSON string of the STIX bundle ready for export.
    """
    from intel.stix_models import STIXConverter
    from backend.models.models import IOC, IOCType, Severity
    from intel.threat_intel import detect_ioc_type

    converter = STIXConverter()
    ioc_type_str = detect_ioc_type(target)

    # Create a minimal IOC object for conversion
    ioc = IOC()
    ioc.value = target
    ioc.ioc_type = ioc_type_str
    ioc.severity = Severity.HIGH if ioc_data.get("malicious") else Severity.INFO
    ioc.confidence = ioc_data.get("reputation", {}).get("confidence", 50)
    ioc.tlp = "AMBER"

    indicator = converter.ioc_to_indicator(ioc)
    if indicator:
        bundle = converter.create_bundle([indicator])
        return bundle.serialize(pretty=True)
    return "{}"


# ── Graph Nodes ───────────────────────────────────────────────────────────────


RECON_AGENT_PROMPT = """You are a Reconnaissance Agent specialized in OSINT gathering.
Your task is to gather comprehensive information about the target: {target}

You have access to these tools:
- run_recon: Gather DNS, WHOIS, subdomains, certificate transparency data
- query_knowledge_graph: Check existing threat intelligence graph

ALWAYS:
1. Start by running reconnaissance on the target
2. Check the knowledge graph for existing information
3. Summarize your findings concisely, focusing on security-relevant data
4. Identify any suspicious or notable findings

Return a structured summary of all findings."""


INTEL_AGENT_PROMPT = """You are a Threat Intelligence Analyst.
You have received reconnaissance results for: {target}

Your task is to:
1. Run threat intelligence enrichment on the target
2. Search the knowledge base for related threats
3. Correlate findings with known threat actors and campaigns
4. Assess the risk level and confidence

Available tools:
- run_threat_intel: Check VirusTotal, AbuseIPDB, GreyNoise, etc.
- search_rag_knowledge: Search threat intelligence database
- create_stix_bundle: Create STIX export if malicious

Provide a threat assessment with:
- Risk level (CRITICAL/HIGH/MEDIUM/LOW/CLEAN)
- Confidence score (0-100)
- Key findings
- Associated threat actors (if any)
- Recommended actions"""


REPORT_AGENT_PROMPT = """You are a Senior Intelligence Report Writer.
Generate a comprehensive, executive-level threat intelligence report.

Target: {target}
Reconnaissance Findings: {recon_summary}
Threat Intelligence: {intel_summary}

Write a professional report with these sections:
1. Executive Summary (3-4 sentences, non-technical)
2. Technical Findings (detailed, for security analysts)
3. Risk Assessment (with score and justification)
4. IOC List (structured, ready for import)
5. Recommendations (prioritized actions)
6. Appendix (raw data references)

Format: Markdown
Tone: Professional security advisory
Length: Comprehensive but concise"""


async def recon_node(state: InvestigationState) -> InvestigationState:
    """Recon Agent: gather initial intelligence."""
    log.info("agent_recon_started", target=state["target"])

    llm = get_llm()
    tools = [run_recon, query_knowledge_graph]
    agent = llm.bind_tools(tools)

    system_msg = SystemMessage(
        content=RECON_AGENT_PROMPT.format(target=state["target"])
    )
    human_msg = HumanMessage(
        content=f"Investigate target: {state['target']}"
    )

    messages = [system_msg, human_msg]
    response = await agent.ainvoke(messages)

    return {
        **state,
        "messages": state["messages"] + [response],
        "recon_results": {"agent_response": response.content},
        "next_action": "intel",
    }


async def intel_node(state: InvestigationState) -> InvestigationState:
    """Intel Agent: threat intelligence enrichment."""
    log.info("agent_intel_started", target=state["target"])

    llm = get_llm()
    tools = [run_threat_intel, search_rag_knowledge, create_stix_bundle]
    agent = llm.bind_tools(tools)

    recon_summary = state["recon_results"].get("agent_response", "No recon data")

    system_msg = SystemMessage(
        content=INTEL_AGENT_PROMPT.format(target=state["target"])
    )
    human_msg = HumanMessage(
        content=f"Perform threat intelligence on: {state['target']}\n\nRecon context: {recon_summary[:2000]}"
    )

    messages = [system_msg, human_msg]
    response = await agent.ainvoke(messages)

    return {
        **state,
        "messages": state["messages"] + [response],
        "intel_results": {"agent_response": response.content},
        "next_action": "report",
    }


async def report_node(state: InvestigationState) -> InvestigationState:
    """Report Agent: generate comprehensive intelligence report."""
    log.info("agent_report_started", target=state["target"])

    llm = get_llm(temperature=0.3)  # Slightly higher temp for better writing

    recon_summary = state["recon_results"].get("agent_response", "")
    intel_summary = state["intel_results"].get("agent_response", "")

    prompt = REPORT_AGENT_PROMPT.format(
        target=state["target"],
        recon_summary=recon_summary[:3000],
        intel_summary=intel_summary[:3000],
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {
        **state,
        "messages": state["messages"] + [response],
        "report": response.content,
        "next_action": END,
    }


def should_continue(state: InvestigationState) -> str:
    """Route to next agent based on state."""
    return state.get("next_action", END)


# ── Investigation Graph ────────────────────────────────────────────────────────


def build_investigation_graph() -> StateGraph:
    """Build the LangGraph investigation workflow."""
    workflow = StateGraph(InvestigationState)

    # Add nodes
    workflow.add_node("recon", recon_node)
    workflow.add_node("intel", intel_node)
    workflow.add_node("report", report_node)

    # Add tool nodes
    recon_tools = ToolNode([run_recon, query_knowledge_graph])
    intel_tools = ToolNode([run_threat_intel, search_rag_knowledge, create_stix_bundle])
    workflow.add_node("recon_tools", recon_tools)
    workflow.add_node("intel_tools", intel_tools)

    # Define edges
    workflow.add_edge(START, "recon")
    workflow.add_conditional_edges("recon", should_continue, {
        "intel": "intel",
        END: END,
    })
    workflow.add_conditional_edges("intel", should_continue, {
        "report": "report",
        END: END,
    })
    workflow.add_edge("report", END)

    return workflow


# ── Main Interface ─────────────────────────────────────────────────────────────


class InvestigationAgent:
    """High-level interface for running autonomous OSINT investigations."""

    def __init__(self) -> None:
        self.graph = build_investigation_graph().compile()

    async def investigate(
        self, target: str, investigation_id: str | None = None
    ) -> dict[str, Any]:
        """
        Run a full autonomous investigation on a target.
        Returns structured results with report and raw data.
        """
        import uuid
        inv_id = investigation_id or str(uuid.uuid4())

        log.info("investigation_started", target=target, id=inv_id)

        initial_state: InvestigationState = {
            "target": target,
            "investigation_id": inv_id,
            "messages": [],
            "recon_results": {},
            "intel_results": {},
            "graph_results": {},
            "analysis": "",
            "report": "",
            "error": None,
            "next_action": "recon",
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)
            log.info("investigation_completed", target=target, id=inv_id)

            return {
                "investigation_id": inv_id,
                "target": target,
                "report": final_state["report"],
                "recon_data": final_state["recon_results"],
                "intel_data": final_state["intel_results"],
                "success": True,
            }
        except Exception as e:
            log.error("investigation_failed", target=target, error=str(e))
            return {
                "investigation_id": inv_id,
                "target": target,
                "success": False,
                "error": str(e),
            }

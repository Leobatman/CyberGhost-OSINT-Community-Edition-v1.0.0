from __future__ import annotations

import asyncio
from typing import Any

import structlog
from sqlalchemy import select
from celery.exceptions import SoftTimeLimitExceeded

from backend.core.database import async_session_factory
from backend.models.models import Scan, ScanResult, IOC, IOCType
from backend.models.stix import StixObject
from intel.knowledge_graph import knowledge_graph
from intel.stix_models import STIXConverter
from intel.threat_intel import detect_ioc_type
from intel.llm_summarizer import InvestigationSummarizer
from workers.celery_app import celery_app

log = structlog.get_logger(__name__)

@celery_app.task(
    name="workers.tasks.sync_tasks.sync_scan_results",
    max_retries=3,
    default_retry_delay=60,
    queue="sync",
    acks_late=True,
)
def sync_scan_results(scan_id: str) -> dict[str, Any]:
    """Sync a completed scan's results to Neo4j Attack Graph and generate STIX in TAXII."""
    log.info("sync_postgres_neo4j_started", scan_id=scan_id)
    try:
        return asyncio.run(_async_sync_scan_results(scan_id))
    except SoftTimeLimitExceeded:
        log.warning("sync_soft_timeout", scan_id=scan_id)
        raise
    except Exception as exc:
        log.error("sync_task_failed", scan_id=scan_id, error=str(exc))
        raise sync_scan_results.retry(exc=exc, countdown=30)

async def _async_sync_scan_results(scan_id: str) -> dict[str, Any]:
    # 1. Fetch from PostgreSQL
    async with async_session_factory() as db:
        scan_res = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = scan_res.scalar_one_or_none()
        if not scan:
            log.warning("sync_scan_not_found", scan_id=scan_id)
            return {"status": "scan_not_found"}

        results_res = await db.execute(select(ScanResult).where(ScanResult.scan_id == scan_id))
        scan_results = results_res.scalars().all()

        if not scan_results:
            return {"status": "no_results"}

        # Extract Tenant ID for Isolation
        tenant_id = str(scan.tenant_id)

        # Connect Neo4j
        await knowledge_graph.connect()
        converter = STIXConverter()
        
        # Base Node (Target)
        target_ioc_type = detect_ioc_type(scan.target)
        target_label = "Domain" if target_ioc_type == "domain" else "IP"
            
        await knowledge_graph.upsert_node(
            label=target_label,
            value=scan.target,
            tenant_id=tenant_id,
            properties={"metadata": {"scan_id": scan_id}}
        )

        iocs_processed = 0
        
        # 2. Extract and Push to Neo4j / STIX
        for result in scan_results:
            if result.module == "recon":
                records = result.data.get("dns_records", [])
                for record in records:
                    ip = record.get("ip")
                    if ip:
                        await knowledge_graph.upsert_node("IP", ip, tenant_id)
                        await knowledge_graph.link_nodes(target_label, scan.target, "IP", ip, "RESOLVES_TO")
                        iocs_processed += 1
                        
            elif result.module == "subdomains":
                subs = result.data.get("subdomains", [])
                for sub in subs:
                    await knowledge_graph.upsert_node("Subdomain", sub, tenant_id)
                    await knowledge_graph.link_nodes("Subdomain", sub, target_label, scan.target, "PART_OF")
                    iocs_processed += 1
                    
            elif result.module == "threat_intel":
                malicious = result.data.get("malicious", False)
                score = result.data.get("reputation", {}).get("score", 0)
                
                await knowledge_graph.upsert_node(
                    label=target_label,
                    value=scan.target,
                    tenant_id=tenant_id,
                    properties={"reputation_score": score, "malicious": malicious}
                )
                
                # Gerar STIX para o target
                ioc_enum = IOCType.DOMAIN if target_ioc_type == "domain" else IOCType.IPV4
                db_ioc = IOC(
                    value=scan.target, 
                    ioc_type=ioc_enum, 
                    malicious=malicious, 
                    reputation_score=score,
                    tenant_id=scan.tenant_id
                )
                stix_observable = converter.ioc_to_stix_observable(db_ioc)
                
                if stix_observable:
                    indicator = converter.create_indicator(db_ioc)
                    if indicator:
                        # Salvar STIX no Postgres (TAXII Collection Source)
                        stix_obj = StixObject(
                            id=indicator.id,
                            tenant_id=scan.tenant_id,
                            type=indicator.type,
                            name=indicator.name,
                            description=indicator.description,
                            pattern=indicator.pattern,
                            pattern_type=indicator.pattern_type,
                            valid_from=indicator.valid_from,
                            object_data=indicator.serialize()
                        )
                        db.add(stix_obj)
                        
        # 3. GenAI - Executive Summary
        summarizer = InvestigationSummarizer()
        scan_dicts = [{"module": r.module, "severity": r.severity, "data": r.data} for r in scan_results]
        
        ai_summary = await summarizer.summarize(scan.target, scan_dicts, [])
        scan.ai_summary = ai_summary
        
        await db.commit()
        await knowledge_graph.disconnect()
        
    log.info("sync_postgres_neo4j_completed", scan_id=scan_id, iocs_processed=iocs_processed)
    return {"status": "success", "iocs_processed": iocs_processed}

"""
CyberGhost OSINT Enterprise — Scan Tasks
Celery tasks for orchestrating OSINT scans asynchronously
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from celery import Task, current_task, shared_task
from celery.exceptions import SoftTimeLimitExceeded

from workers.celery_app import celery_app

log = structlog.get_logger(__name__)


class ScanTask(Task):
    """Base task class with DB session management."""

    _db_session = None

    def after_return(self, status: str, retval: Any, task_id: str, args: Any, kwargs: Any, einfo: Any) -> None:
        """Cleanup after task execution."""
        if self._db_session:
            asyncio.run(self._db_session.close())
            self._db_session = None


@celery_app.task(
    bind=True,
    base=ScanTask,
    name="workers.tasks.scan_tasks.run_scan",
    max_retries=3,
    default_retry_delay=30,
    queue="recon",
    acks_late=True,
    reject_on_worker_lost=True,
)
def run_scan(self: ScanTask, scan_id: str, target: str, scan_type: str) -> dict[str, Any]:
    """
    Main scan orchestration task.
    Dispatches sub-tasks based on scan_type.
    """
    log.info("scan_task_started", scan_id=scan_id, target=target, type=scan_type)

    try:
        return asyncio.run(
            _async_run_scan(scan_id, target, scan_type)
        )
    except SoftTimeLimitExceeded:
        log.warning("scan_soft_timeout", scan_id=scan_id)
        asyncio.run(
            _update_scan_status(scan_id, "failed", "Scan timed out")
        )
        raise
    except Exception as exc:
        log.error("scan_task_failed", scan_id=scan_id, error=str(exc))
        asyncio.run(
            _update_scan_status(scan_id, "failed", str(exc))
        )
        raise self.retry(exc=exc, countdown=30)


async def _async_run_scan(scan_id: str, target: str, scan_type: str) -> dict[str, Any]:
    """Async scan execution — runs sub-modules in parallel where possible."""
    from sqlalchemy import select
    from backend.core.database import async_session_factory
    from backend.models.models import Scan, ScanStatus

    async with async_session_factory() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(UTC)
        await db.commit()

    results: dict[str, Any] = {}
    start_time = datetime.now(UTC)

    try:
        if scan_type == "full":
            # Parallel execution of all modules
            tasks = await asyncio.gather(
                _run_recon_module(target),
                _run_threat_intel_module(target),
                _run_subdomain_module(target),
                _run_cert_transparency_module(target),
                _run_web_recon_module(target),
                _run_vuln_scanner_module(target),
                _run_passive_dns_module(target),
                _run_asn_module(target),
                return_exceptions=True,
            )
            module_keys = [
                "recon", "threat_intel", "subdomains", "cert_transparency", 
                "web_recon", "vuln_scanner", "passive_dns", "asn"
            ]
            
            for key, task_result in zip(module_keys, tasks):
                if isinstance(task_result, Exception):
                    log.error(f"module_error_{key}", scan_id=scan_id, error=str(task_result))
                    results[key] = {"error": str(task_result)}
                else:
                    results[key] = task_result

        else:
            # Single module execution based on scan_type
            module_map = {
                "recon": _run_recon_module,
                "threat_intel": _run_threat_intel_module,
                "subdomain": _run_subdomain_module,
                "cert_transparency": _run_cert_transparency_module,
                "passive_dns": _run_passive_dns_module,
                "asn": _run_asn_module,
                "web_recon": _run_web_recon_module,
                "vuln_scan": _run_vuln_scanner_module
            }
            if scan_type in module_map:
                results[scan_type] = await module_map[scan_type](target)
            else:
                results["error"] = f"Unknown scan_type: {scan_type}"

    except Exception as e:
        log.error("scan_orchestration_error", scan_id=scan_id, error=str(e))
        results["error"] = str(e)

    # Save results and update scan status
    duration = int((datetime.now(UTC) - start_time).total_seconds())
    await _finalize_scan(scan_id, results, duration)

    return {"scan_id": scan_id, "results": results, "duration": duration}


async def _run_recon_module(target: str) -> dict[str, Any]:
    """Run basic recon: DNS, WHOIS, headers."""
    from recon.dns_intel import DNSIntelligence
    dns = DNSIntelligence()
    return await dns.analyze(target)


async def _run_threat_intel_module(target: str) -> dict[str, Any]:
    """Run threat intelligence lookup — PARALLEL API calls."""
    from intel.threat_intel import ThreatIntelligence
    ti = ThreatIntelligence()
    return await ti.enrich(target)


async def _run_subdomain_module(target: str) -> dict[str, Any]:
    """Run subdomain enumeration."""
    from recon.subdomain_enum import SubdomainEnumerator
    se = SubdomainEnumerator()
    return await se.enumerate(target)


async def _run_cert_transparency_module(target: str) -> dict[str, Any]:
    """Run certificate transparency lookup."""
    from recon.cert_transparency import CertificateTransparency
    ct = CertificateTransparency()
    return await ct.lookup(target)


async def _run_passive_dns_module(target: str) -> dict[str, Any]:
    """Run passive DNS lookup."""
    from recon.passive_dns import PassiveDNS
    pdns = PassiveDNS()
    return await pdns.lookup(target)


async def _run_asn_module(target: str) -> dict[str, Any]:
    """Run ASN intelligence lookup."""
    from recon.asn_intel import ASNIntelligence
    asn = ASNIntelligence()
    return await asn.lookup(target)


async def _run_web_recon_module(target: str) -> dict[str, Any]:
    """Run Web HTTP checks (headers, robots, WAF)."""
    from recon.web_recon import WebRecon
    wr = WebRecon()
    return await wr.analyze(target)


async def _run_vuln_scanner_module(target: str) -> dict[str, Any]:
    """Run Vulnerability and secrets scanner."""
    from recon.vuln_scanner import VulnScanner
    vs = VulnScanner()
    return await vs.analyze(target)


async def _update_scan_status(
    scan_id: str, status: str, error: str | None = None
) -> None:
    """Update scan status in database."""
    from sqlalchemy import select
    from backend.core.database import async_session_factory
    from backend.models.models import Scan, ScanStatus

    async with async_session_factory() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan:
            scan.status = ScanStatus(status)
            if error:
                scan.error_message = str(error)[:1000]  # Truncate
            scan.completed_at = datetime.now(UTC)
            await db.commit()


async def _finalize_scan(
    scan_id: str, results: dict[str, Any], duration: int
) -> None:
    """Save all results and mark scan as completed safely."""
    from sqlalchemy import select
    from backend.core.database import async_session_factory
    from backend.models.models import Scan, ScanResult, ScanStatus, Severity

    async with async_session_factory() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if not scan:
            return

        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.now(UTC)
        scan.duration_seconds = duration

        # Save results per module safely handling potential serialization issues
        for module_name, module_data in results.items():
            if isinstance(module_data, dict) and "error" not in module_data:
                # Sanitize dict for pgjsonb (remove non-string keys, recursive obj conversions if needed)
                # Currently trusting the module's analyze() returns JSON-serializable output
                result_record = ScanResult(
                    scan_id=scan.id,
                    module=module_name,
                    severity=Severity.INFO,
                    title=f"{module_name.replace('_', ' ').title()} Results",
                    data=module_data,
                )
                db.add(result_record)

        await db.commit()
        log.info("scan_finalized", scan_id=scan_id, duration=duration)
        
        # Dispatch sync to Graph DB and STIX
        from workers.tasks.sync_tasks import sync_scan_results
        try:
            sync_scan_results.apply_async(args=[scan_id])
            log.info("sync_task_dispatched", scan_id=scan_id)
        except Exception as e:
            log.error("sync_task_dispatch_failed", scan_id=scan_id, error=str(e))



@celery_app.task(name="workers.tasks.scan_tasks.cleanup_expired_results")
def cleanup_expired_results() -> dict[str, int]:
    """Periodic task: clean up old scan results."""
    return asyncio.run(_async_cleanup())


async def _async_cleanup() -> dict[str, int]:
    from datetime import timedelta
    from sqlalchemy import delete, select
    from backend.core.database import async_session_factory
    from backend.models.models import Scan, ScanStatus

    cutoff = datetime.now(UTC) - timedelta(days=30)
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scan).where(
                Scan.created_at < cutoff,
                Scan.status.in_([ScanStatus.COMPLETED, ScanStatus.FAILED]),
            )
        )
        old_scans = result.scalars().all()
        count = len(old_scans)
        for scan in old_scans:
            await db.delete(scan)
        await db.commit()

    log.info("cleanup_completed", deleted=count)
    return {"deleted": count}

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
                return_exceptions=True,
            )
            results["recon"] = tasks[0] if not isinstance(tasks[0], Exception) else {"error": str(tasks[0])}
            results["threat_intel"] = tasks[1] if not isinstance(tasks[1], Exception) else {"error": str(tasks[1])}
            results["subdomains"] = tasks[2] if not isinstance(tasks[2], Exception) else {"error": str(tasks[2])}
            results["cert_transparency"] = tasks[3] if not isinstance(tasks[3], Exception) else {"error": str(tasks[3])}

        elif scan_type == "recon":
            results["recon"] = await _run_recon_module(target)
        elif scan_type == "threat_intel":
            results["threat_intel"] = await _run_threat_intel_module(target)
        elif scan_type == "subdomain":
            results["subdomains"] = await _run_subdomain_module(target)
        elif scan_type == "cert_transparency":
            results["cert_transparency"] = await _run_cert_transparency_module(target)
        elif scan_type == "passive_dns":
            results["passive_dns"] = await _run_passive_dns_module(target)
        elif scan_type == "asn":
            results["asn"] = await _run_asn_module(target)

    except Exception as e:
        log.error("scan_module_error", scan_id=scan_id, error=str(e))
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
                scan.error_message = error[:1000]  # Truncate
            scan.completed_at = datetime.now(UTC)
            await db.commit()


async def _finalize_scan(
    scan_id: str, results: dict[str, Any], duration: int
) -> None:
    """Save all results and mark scan as completed."""
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

        # Save results per module
        for module_name, module_data in results.items():
            if isinstance(module_data, dict) and "error" not in module_data:
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

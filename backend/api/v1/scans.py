"""
CyberGhost OSINT Enterprise — Scans Router
Full CRUD with RBAC + input validation + no injection possible
"""
from __future__ import annotations

import re
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.deps import get_client_ip, require_permission
from backend.core.security import Permission, Role, audit_log
from backend.models.models import Scan, ScanResult, ScanStatus, ScanType, Severity, User
from backend.schemas.auth import (
    ResultResponse,
    ScanCreateRequest,
    ScanListResponse,
    ScanResponse,
)
from workers.celery_app import celery_app
from workers.tasks.scan_tasks import run_scan

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/scans", tags=["Scans"])

# ── Target Validation ─────────────────────────────────────────────────────────

_IP_RE = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$"
)
_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
_HASH_RE = re.compile(r"^[a-fA-F0-9]{32,64}$")
_URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")

# Dangerous characters that should never appear in targets
_DANGEROUS = re.compile(r"[;&|`$\\<>'\"]")


def validate_target(target: str) -> str:
    """
    Validate and normalize scan target.
    Raises ValueError for invalid or dangerous inputs.
    """
    target = target.strip().lower()

    if not target:
        raise ValueError("Target cannot be empty")

    if len(target) > 512:
        raise ValueError("Target too long (max 512 chars)")

    # Reject shell injection characters
    if _DANGEROUS.search(target):
        raise ValueError(f"Target contains forbidden characters")

    # Must match one of the accepted formats
    if not any([
        _IP_RE.match(target),
        _DOMAIN_RE.match(target),
        _EMAIL_RE.match(target),
        _HASH_RE.match(target),
        _URL_RE.match(target.lower()),
    ]):
        raise ValueError(
            "Target must be a valid IP, domain, email, hash, or URL"
        )

    return target


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("", response_model=ScanResponse, status_code=201)
async def create_scan(
    request: Request,
    body: ScanCreateRequest,
    current_user: Annotated[User, Depends(require_permission(Permission.SCAN_CREATE))],
    db: AsyncSession = Depends(get_db),
) -> Scan:
    """Create and queue a new scan."""
    # Validate target strictly
    try:
        validated_target = validate_target(body.target)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    # Validate scan type
    try:
        scan_type = ScanType(body.scan_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid scan type. Valid: {[t.value for t in ScanType]}",
        )

    # Create scan record
    scan = Scan(
        user_id=current_user.id,
        target=validated_target,
        scan_type=scan_type,
        status=ScanStatus.QUEUED,
        priority=body.priority,
        config=body.config,
    )
    db.add(scan)
    await db.flush()
    await db.refresh(scan)

    # Dispatch to Celery
    try:
        task = run_scan.apply_async(
            args=[str(scan.id), validated_target, scan_type.value],
            priority=body.priority,
        )
        scan.celery_task_id = task.id
        await db.commit()
    except Exception as e:
        log.error("celery_dispatch_failed", error=str(e), scan_id=str(scan.id))
        scan.status = ScanStatus.FAILED
        scan.error_message = f"Failed to queue scan: {e}"
        await db.commit()

    audit_log(
        "scan_created",
        str(current_user.id),
        get_client_ip(request),
        resource=validated_target,
        details={"scan_id": str(scan.id), "type": scan_type.value},
    )
    log.info("scan_created", scan_id=str(scan.id), target=validated_target)
    return scan


@router.get("", response_model=ScanListResponse)
async def list_scans(
    current_user: Annotated[User, Depends(require_permission(Permission.SCAN_READ))],
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    scan_type_filter: str | None = Query(default=None, alias="type"),
) -> ScanListResponse:
    """List scans for current user with pagination and filtering."""
    query = select(Scan)

    # Non-admins only see their own scans
    if current_user.role not in (Role.ADMIN, Role.SUPER_ADMIN):
        query = query.where(Scan.user_id == current_user.id)

    if status_filter:
        try:
            query = query.where(Scan.status == ScanStatus(status_filter))
        except ValueError:
            raise HTTPException(422, detail=f"Invalid status: {status_filter}")

    if scan_type_filter:
        try:
            query = query.where(Scan.scan_type == ScanType(scan_type_filter))
        except ValueError:
            raise HTTPException(422, detail=f"Invalid type: {scan_type_filter}")

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Paginate
    query = query.order_by(Scan.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    scans = list(result.scalars().all())

    return ScanListResponse(
        items=[ScanResponse.model_validate(s) for s in scans],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: UUID,
    current_user: Annotated[User, Depends(require_permission(Permission.SCAN_READ))],
    db: AsyncSession = Depends(get_db),
) -> Scan:
    """Get a specific scan by ID."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Ownership check for non-admins
    if (
        current_user.role not in (Role.ADMIN, Role.SUPER_ADMIN)
        and scan.user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    return scan


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(
    request: Request,
    scan_id: UUID,
    current_user: Annotated[User, Depends(require_permission(Permission.SCAN_DELETE))],
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a scan and all its results."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if (
        current_user.role not in (Role.ADMIN, Role.SUPER_ADMIN)
        and scan.user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(scan)
    audit_log(
        "scan_deleted", str(current_user.id), get_client_ip(request),
        resource=str(scan_id)
    )


@router.post("/{scan_id}/stop", response_model=ScanResponse)
async def stop_scan(
    request: Request,
    scan_id: UUID,
    current_user: Annotated[User, Depends(require_permission(Permission.SCAN_STOP))],
    db: AsyncSession = Depends(get_db),
) -> Scan:
    """Stop a running scan."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status not in (ScanStatus.RUNNING, ScanStatus.QUEUED):
        raise HTTPException(422, detail="Scan is not running")

    # Revoke Celery task
    if scan.celery_task_id:
        try:
            celery_app.control.revoke(scan.celery_task_id, terminate=True)
        except Exception as e:
            log.warning("celery_revoke_failed", error=str(e))

    scan.status = ScanStatus.CANCELLED
    await db.commit()

    audit_log("scan_stopped", str(current_user.id), get_client_ip(request))
    return scan


@router.get("/{scan_id}/results", response_model=list[ResultResponse])
async def get_scan_results(
    scan_id: UUID,
    current_user: Annotated[User, Depends(require_permission(Permission.SCAN_READ))],
    db: AsyncSession = Depends(get_db),
    severity: str | None = None,
    module: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=500),
) -> list[ScanResult]:
    """Get results for a specific scan."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if (
        current_user.role not in (Role.ADMIN, Role.SUPER_ADMIN)
        and scan.user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(ScanResult).where(ScanResult.scan_id == scan_id)

    if severity:
        try:
            query = query.where(ScanResult.severity == Severity(severity))
        except ValueError:
            raise HTTPException(422, detail=f"Invalid severity: {severity}")

    if module:
        query = query.where(ScanResult.module == module)

    query = query.order_by(ScanResult.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    return list(result.scalars().all())

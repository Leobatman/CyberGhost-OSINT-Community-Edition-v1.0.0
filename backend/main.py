"""
CyberGhost OSINT Enterprise — FastAPI Application
Main entry point with all middleware, routers, and observability
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator

from backend.api.v1.auth import router as auth_router
from backend.api.v1.scans import router as scans_router
from backend.api.v1.stix import router as stix_router
from backend.api.v1.taxii import router as taxii_router
from backend.core.config import settings
from backend.core.database import check_database_health, create_all_tables

log = structlog.get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """Application startup and shutdown."""
    log.info(
        "app_starting",
        version=settings.app_version,
        environment=settings.app_env,
    )

    # Setup OpenTelemetry
    _setup_telemetry()

    # Database initialization
    await create_all_tables()
    log.info("database_ready")

    yield  # Application runs here

    log.info("app_stopping")


def _setup_telemetry() -> None:
    """Initialize OpenTelemetry tracing."""
    try:
        resource = Resource.create(
            {
                "service.name": settings.observability.service_name,
                "deployment.environment": settings.observability.environment,
                "service.version": settings.app_version,
            }
        )
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(
            endpoint=settings.observability.otlp_endpoint, insecure=True
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        log.info("telemetry_initialized")
    except Exception as e:
        log.warning("telemetry_setup_failed", error=str(e))


# ── App Factory ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="CyberGhost OSINT Enterprise Platform — API Documentation",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters — first added, last executed) ───────────────

    # Trusted hosts — prevents Host header injection
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.cors_origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # Security headers
    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        return response

    # Request ID + timing
    @app.middleware("http")
    async def request_context(request: Request, call_next: Any) -> Response:
        import uuid
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()

        with structlog.contextvars.bound_contextvars(request_id=request_id):
            response = await call_next(request)

        duration = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        log.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration, 2),
        )
        return response

    # Rate limiting (Redis-based per IP)
    @app.middleware("http")
    async def rate_limit(request: Request, call_next: Any) -> Response:
        # Skip health checks
        if request.url.path in ("/api/health", "/api/ready", "/metrics"):
            return await call_next(request)

        try:
            import redis.asyncio as aioredis
            from backend.core.deps import get_client_ip

            ip = get_client_ip(request)
            r = aioredis.from_url(settings.redis.url)
            key = f"rate_limit:{ip}"
            pipe = r.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)
            results = await pipe.execute()
            count = results[0]
            await r.aclose()

            if count > settings.rate_limit_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": "60"},
                )
        except Exception:
            pass  # Fail open if Redis unavailable

        return await call_next(request)

    # ── Routers ───────────────────────────────────────────────────────────────

    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(scans_router, prefix=api_prefix)
    app.include_router(stix_router, prefix=api_prefix)
    app.include_router(taxii_router, prefix=api_prefix)

    # ── System Endpoints ──────────────────────────────────────────────────────

    @app.get("/api/health", include_in_schema=False)
    async def health() -> dict[str, Any]:
        db_health = await check_database_health()
        all_healthy = db_health["status"] == "healthy"
        return JSONResponse(
            status_code=200 if all_healthy else 503,
            content={
                "status": "healthy" if all_healthy else "degraded",
                "version": settings.app_version,
                "environment": settings.app_env,
                "timestamp": datetime.now(UTC).isoformat(),
                "services": {
                    "database": db_health["status"],
                },
            },
        )

    @app.get("/api/ready", include_in_schema=False)
    async def ready() -> dict[str, str]:
        """Kubernetes readiness probe."""
        return {"status": "ready"}

    # ── Prometheus Metrics ────────────────────────────────────────────────────
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/api/health", "/api/ready"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # ── OpenTelemetry Instrumentation ─────────────────────────────────────────
    FastAPIInstrumentor.instrument_app(app)

    return app


app = create_app()

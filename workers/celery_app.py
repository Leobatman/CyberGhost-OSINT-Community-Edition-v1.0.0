"""
CyberGhost OSINT Enterprise — Celery Application
Queue configuration, task routing, monitoring
"""
from __future__ import annotations

from celery import Celery
from celery.signals import after_setup_logger, worker_ready
from kombu import Exchange, Queue

from backend.core.config import settings

# ── Celery App ────────────────────────────────────────────────────────────────

celery_app = Celery(
    "cyberghost",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=[
        "workers.tasks.scan_tasks",
        "workers.tasks.intel_tasks",
        "workers.tasks.recon_tasks",
        "workers.tasks.report_tasks",
    ],
)

# ── Queues ────────────────────────────────────────────────────────────────────

default_exchange = Exchange("default", type="direct")
recon_exchange = Exchange("recon", type="direct")
intel_exchange = Exchange("intel", type="direct")
ai_exchange = Exchange("ai", type="direct")

celery_app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default", max_priority=10),
    Queue("recon", recon_exchange, routing_key="recon", max_priority=10),
    Queue("intel", intel_exchange, routing_key="intel", max_priority=10),
    Queue("ai", ai_exchange, routing_key="ai", max_priority=5),
    Queue("reports", default_exchange, routing_key="reports", max_priority=3),
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"

# ── Task Routing ──────────────────────────────────────────────────────────────

celery_app.conf.task_routes = {
    "workers.tasks.scan_tasks.*": {"queue": "recon"},
    "workers.tasks.intel_tasks.*": {"queue": "intel"},
    "workers.tasks.recon_tasks.*": {"queue": "recon"},
    "workers.tasks.report_tasks.*": {"queue": "reports"},
}

# ── Configuration ─────────────────────────────────────────────────────────────

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Performance
    worker_prefetch_multiplier=1,  # Fair task distribution
    task_acks_late=True,           # Ack after task completion
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (memory leak prevention)
    task_compression="gzip",

    # Timeouts
    task_soft_time_limit=settings.celery.task_soft_time_limit,
    task_time_limit=settings.celery.task_time_limit,

    # Priority
    task_queue_max_priority=10,
    task_default_priority=5,

    # Results
    result_expires=86400,  # 24h
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_policy": {"timeout": 5.0},
    },

    # Beat (scheduler)
    beat_schedule={
        "cleanup-expired-cache": {
            "task": "workers.tasks.scan_tasks.cleanup_expired_results",
            "schedule": 3600.0,  # Every hour
        },
        "update-threat-feeds": {
            "task": "workers.tasks.intel_tasks.update_threat_feeds",
            "schedule": 21600.0,  # Every 6 hours
        },
    },
)


# ── Signals ───────────────────────────────────────────────────────────────────


@worker_ready.connect
def on_worker_ready(sender: Any, **kwargs: Any) -> None:  # type: ignore[name-defined]
    import structlog
    log = structlog.get_logger(__name__)
    log.info("celery_worker_ready", hostname=sender.hostname)


@after_setup_logger.connect
def setup_loggers(logger: Any, **kwargs: Any) -> None:  # type: ignore[name-defined]
    """Configure structured logging for Celery."""
    import logging
    import structlog

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

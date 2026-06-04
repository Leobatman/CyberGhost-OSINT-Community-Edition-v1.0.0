from workers.celery_app import celery_app
import structlog

log = structlog.get_logger(__name__)

@celery_app.task(name="workers.tasks.sync_tasks.sync_ioc_to_neo4j")
def sync_ioc_to_neo4j(ioc_id: str):
    """Sync an IOC from PostgreSQL to Neo4j."""
    log.info("sync_postgres_neo4j_started", ioc_id=ioc_id)
    # Placeholder for actual sync logic
    # 1. Fetch from PostgreSQL
    # 2. Push to Neo4j via KnowledgeGraph.upsert_ioc
    pass

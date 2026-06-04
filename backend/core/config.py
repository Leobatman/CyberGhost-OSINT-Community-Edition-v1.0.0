"""
CyberGhost OSINT Enterprise — Core Configuration
Todas as configurações via Pydantic Settings. Zero hardcoded values.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DatabaseSettings(BaseSettings):
    url: PostgresDsn = Field(
        default="postgresql+asyncpg://cyberghost:password@localhost:5432/cyberghost",
        alias="DATABASE_URL",
    )
    pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=40, alias="DATABASE_MAX_OVERFLOW")
    echo: bool = Field(default=False, alias="DATABASE_ECHO")


class RedisSettings(BaseSettings):
    url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    cache_ttl: int = Field(default=3600, alias="REDIS_CACHE_TTL")


class CelerySettings(BaseSettings):
    broker_url: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_BROKER_URL"
    )
    result_backend: str = Field(
        default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND"
    )
    max_workers: int = Field(default=10, alias="CELERY_MAX_WORKERS")
    task_soft_time_limit: int = 300
    task_time_limit: int = 600


class JWTSettings(BaseSettings):
    secret_key: SecretStr = Field(
        default="changeme-64-char-secret", alias="JWT_SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )


class ElasticsearchSettings(BaseSettings):
    url: str = Field(default="https://localhost:9200", alias="ELASTICSEARCH_URL")
    username: str = Field(default="elastic", alias="ELASTICSEARCH_USERNAME")
    password: SecretStr = Field(default="changeme", alias="ELASTICSEARCH_PASSWORD")
    ca_cert: str | None = Field(default=None, alias="ELASTICSEARCH_CA_CERT")


class Neo4jSettings(BaseSettings):
    uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    password: SecretStr = Field(default="changeme", alias="NEO4J_PASSWORD")
    database: str = Field(default="cyberghost", alias="NEO4J_DATABASE")


class QdrantSettings(BaseSettings):
    url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    api_key: SecretStr | None = Field(default=None, alias="QDRANT_API_KEY")
    collection: str = Field(
        default="cyberghost_knowledge", alias="QDRANT_COLLECTION"
    )


class AISettings(BaseSettings):
    provider: Literal["ollama", "openai", "anthropic", "auto"] = Field(
        default="ollama", alias="AI_PROVIDER"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="llama3.2:3b", alias="OLLAMA_MODEL")
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: SecretStr | None = Field(
        default=None, alias="ANTHROPIC_API_KEY"
    )
    embedding_model: str = Field(
        default="nomic-embed-text", alias="EMBEDDING_MODEL"
    )


class OsintApiKeys(BaseSettings):
    shodan: SecretStr | None = Field(default=None, alias="SHODAN_API_KEY")
    virustotal: SecretStr | None = Field(default=None, alias="VIRUSTOTAL_API_KEY")
    censys_id: SecretStr | None = Field(default=None, alias="CENSYS_API_ID")
    censys_secret: SecretStr | None = Field(default=None, alias="CENSYS_API_SECRET")
    greynoise: SecretStr | None = Field(default=None, alias="GREYNOISE_API_KEY")
    hunter: SecretStr | None = Field(default=None, alias="HUNTER_API_KEY")
    securitytrails: SecretStr | None = Field(
        default=None, alias="SECURITYTRAILS_API_KEY"
    )
    zoomeye: SecretStr | None = Field(default=None, alias="ZOOMEYE_API_KEY")
    binaryedge: SecretStr | None = Field(default=None, alias="BINARYEDGE_API_KEY")
    hibp: SecretStr | None = Field(default=None, alias="HIBP_API_KEY")
    emailrep: SecretStr | None = Field(default=None, alias="EMAILREP_API_KEY")
    github: SecretStr | None = Field(default=None, alias="GITHUB_API_KEY")
    abuseipdb: SecretStr | None = Field(default=None, alias="ABUSEIPDB_API_KEY")
    alienvault_otx: SecretStr | None = Field(
        default=None, alias="ALIENVAULT_OTX_API_KEY"
    )
    ibm_xforce_key: SecretStr | None = Field(
        default=None, alias="IBM_XFORCE_API_KEY"
    )
    ibm_xforce_pass: SecretStr | None = Field(
        default=None, alias="IBM_XFORCE_API_PASSWORD"
    )


class ObservabilitySettings(BaseSettings):
    otlp_endpoint: str = Field(
        default="http://localhost:4317", alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    service_name: str = Field(
        default="cyberghost-backend", alias="OTEL_SERVICE_NAME"
    )
    environment: str = Field(default="development", alias="OTEL_ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: Literal["json", "console"] = Field(
        default="json", alias="LOG_FORMAT"
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="CyberGhost OSINT Enterprise", alias="APP_NAME")
    app_version: str = Field(default="8.0.0", alias="APP_VERSION")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: SecretStr = Field(
        default="changeme-app-secret", alias="SECRET_KEY"
    )
    allowed_hosts: list[str] = Field(default=["localhost", "127.0.0.1"])
    cors_origins: list[AnyHttpUrl] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, alias="RATE_LIMIT_BURST")

    # Sub-settings (nested via environment-prefixed variables)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    elasticsearch: ElasticsearchSettings = Field(
        default_factory=ElasticsearchSettings
    )
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    ai: AISettings = Field(default_factory=AISettings)
    api_keys: OsintApiKeys = Field(default_factory=OsintApiKeys)
    observability: ObservabilitySettings = Field(
        default_factory=ObservabilitySettings
    )

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [h.strip() for h in v.split(",")]
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance — cached after first call."""
    return Settings()


settings = get_settings()

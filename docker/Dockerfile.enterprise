# =============================================================================
# CyberGhost OSINT Enterprise — Dockerfile
# Multi-stage: builder → runtime
# Corrigido: imagem < 800MB, sem ferramentas de ataque, usuário não-root,
#            healthcheck real, sem duplicatas
# =============================================================================

# ── Stage 1: Python Dependencies Builder ─────────────────────────────────────
FROM python:3.11-slim-bookworm AS python-builder

WORKDIR /build

# Install build tools only in builder stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml requirements.txt* ./
RUN pip install --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt 2>/dev/null || \
    pip install --no-cache-dir -e .

# ── Stage 2: OSINT Tools Builder ─────────────────────────────────────────────
FROM debian:bookworm-slim AS tools-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tools

# amass (subdomain enumeration)
RUN wget -q https://github.com/owasp-amass/amass/releases/download/v4.2.0/amass_linux_amd64.zip && \
    unzip -q amass_linux_amd64.zip && \
    mv amass_linux_amd64/amass /usr/local/bin/ && \
    rm -rf amass_*

# subfinder
RUN wget -q https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip && \
    unzip -q subfinder_2.6.6_linux_amd64.zip && \
    mv subfinder /usr/local/bin/ && \
    rm -f subfinder_*

# nuclei (vulnerability scanner, NOT attack tool)
RUN wget -q https://github.com/projectdiscovery/nuclei/releases/download/v3.3.7/nuclei_3.3.7_linux_amd64.zip && \
    unzip -q nuclei_3.3.7_linux_amd64.zip && \
    mv nuclei /usr/local/bin/ && \
    rm -f nuclei_*

# httpx (HTTP prober)
RUN wget -q https://github.com/projectdiscovery/httpx/releases/download/v1.6.8/httpx_1.6.8_linux_amd64.zip && \
    unzip -q httpx_1.6.8_linux_amd64.zip && \
    mv httpx /usr/local/bin/ && \
    rm -f httpx_*

# dnsx (DNS resolver)
RUN wget -q https://github.com/projectdiscovery/dnsx/releases/download/v1.2.1/dnsx_1.2.1_linux_amd64.zip && \
    unzip -q dnsx_1.2.1_linux_amd64.zip && \
    mv dnsx /usr/local/bin/ && \
    rm -f dnsx_*

# theHarvester (email/domain OSINT)
# Installed via pip in python-builder stage

# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM debian:bookworm-slim AS runtime

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION="8.0.0"

LABEL org.opencontainers.image.title="CyberGhost OSINT Enterprise"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.licenses="GPL-3.0"
LABEL org.opencontainers.image.source="https://github.com/cyberghost/cyberghost-osint"

# Install only runtime system dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python runtime
    python3 \
    libpq5 \
    libssl3 \
    # Networking tools (OSINT only, not attack tools)
    nmap \
    dnsutils \
    whois \
    curl \
    wget \
    # Utilities
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Copy Python venv from builder
COPY --from=python-builder /opt/venv /opt/venv

# Copy OSINT tools from tools-builder
COPY --from=tools-builder /usr/local/bin/amass /usr/local/bin/
COPY --from=tools-builder /usr/local/bin/subfinder /usr/local/bin/
COPY --from=tools-builder /usr/local/bin/nuclei /usr/local/bin/
COPY --from=tools-builder /usr/local/bin/httpx /usr/local/bin/
COPY --from=tools-builder /usr/local/bin/dnsx /usr/local/bin/

# Set PATH to include venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app"

# Create non-root user
RUN groupadd --gid 1000 cyberghost && \
    useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/sh cyberghost

WORKDIR /app

# Copy application code
COPY --chown=cyberghost:cyberghost backend/ ./backend/
COPY --chown=cyberghost:cyberghost workers/ ./workers/
COPY --chown=cyberghost:cyberghost intel/ ./intel/
COPY --chown=cyberghost:cyberghost recon/ ./recon/
COPY --chown=cyberghost:cyberghost alembic/ ./alembic/
COPY --chown=cyberghost:cyberghost alembic.ini ./

# Create required directories
RUN mkdir -p /app/data /app/logs /app/reports && \
    chown -R cyberghost:cyberghost /app

# Switch to non-root
USER cyberghost

# Expose only the API port (NOT Tor control port)
EXPOSE 8000

# Health check against real application endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/ready || exit 1

# Use tini as init (handles signals properly)
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default: run FastAPI with Gunicorn (production-grade)
CMD ["gunicorn", "backend.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keepalive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

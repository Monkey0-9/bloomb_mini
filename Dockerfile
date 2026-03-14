# ─────────────────────────────────────────────────────────
# SatTrade — Multi-stage Docker Build
# Target: Python 3.11 with GDAL + ML dependencies
# ─────────────────────────────────────────────────────────

# Stage 1: Builder
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /build

# Install Python dependencies first (layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install -e ".[dev]" 2>/dev/null || \
    pip install --no-cache-dir --prefix=/install pydantic numpy scipy requests pyyaml

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal32 \
    libgeos3.12.1 \
    libproj25 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r sattrade && useradd -r -g sattrade -d /app sattrade

WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY agents/ ./agents/
COPY pyproject.toml ./

# Ensure directories exist
RUN mkdir -p /app/data/raw /app/data/processed /app/data/features \
    /app/logs /app/mlruns \
    && chown -R sattrade:sattrade /app

USER sattrade

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "from src.common.config import load_constraints; load_constraints()" || exit 1

# Default: run the pipeline orchestrator
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m"]
CMD ["src.ingest.sentinel"]

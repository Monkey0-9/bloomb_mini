# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgdal-dev gdal-bin \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir build wheel
RUN pip install --no-cache-dir -e ".[dev]" --prefix=/install

# Stage 2: Runtime image
FROM python:3.11-slim AS runtime

# Never run as root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Install only runtime OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal32 gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser tests/ ./tests/
COPY --chown=appuser:appuser demo_full_system.py .
COPY --chown=appuser:appuser pyproject.toml .

USER appuser

# Smoke test: run pytest on container start
CMD ["pytest", "tests/", "-v", "--tb=short"]

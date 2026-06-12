FROM python:3.10-slim

LABEL maintainer="wc2026"
LABEL description="2026 World Cup calibrated PMF prediction engine"
LABEL org.opencontainers.image.source="https://github.com/Risky-Scout/worldcup2026-model"

# System build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (maximises Docker layer cache)
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e "." 2>/dev/null \
    || pip install --no-cache-dir \
        "penaltyblog>=1.11.0" \
        "pandas>=2.0" \
        "pyarrow>=14.0" \
        "scipy>=1.11" \
        "pydantic>=2.0" \
        "click>=8.0" \
        "requests>=2.31" \
        "python-dotenv>=1.0" \
        "python-dateutil>=2.8" \
        "numpy>=1.24"

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY Makefile ./
COPY .env.example ./

# Install package in editable mode
RUN pip install --no-cache-dir -e .

# Persistent data directories (mount these as volumes in production)
RUN mkdir -p \
    data/raw/bdl/2018 \
    data/raw/bdl/2022 \
    data/raw/bdl/2026 \
    data/processed/v1 \
    data/predictions \
    data/published \
    data/clv/2026 \
    reports

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV WC2026_DATA_ROOT=/app/data

# Health check: verify the CLI is importable
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from wc2026.cli import cli; print('OK')" || exit 1

VOLUME ["/app/data", "/app/reports"]

ENTRYPOINT ["python", "-m", "wc2026.cli"]
CMD ["--help"]

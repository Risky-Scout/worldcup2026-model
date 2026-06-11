FROM python:3.10-slim

LABEL maintainer="wc2026"
LABEL description="2026 World Cup calibrated PMF prediction engine"

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cache layer)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "." 2>/dev/null || pip install --no-cache-dir penaltyblog==1.11.0 pandas pyarrow scipy pydantic click requests python-dotenv python-dateutil orjson structlog

# Copy source
COPY src/ ./src/
COPY .env.example ./.env.example

# Data directories
RUN mkdir -p data/raw/bdl data/processed data/predictions data/published reports

# Install package
RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "wc2026.cli"]
CMD ["--help"]

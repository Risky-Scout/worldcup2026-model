#!/bin/bash
# Hard gate: critical path modules must have ≥70% coverage
# Run after the main test suite
set -e
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3.10}"

echo "=== Critical module coverage check ==="
$PYTHON -m pytest tests/ \
  --override-ini="addopts=" \
  --cov=src/wc2026/publishing \
  --cov=src/wc2026/data/snapshot_store \
  --cov=src/wc2026/data/asof_join \
  --cov=src/wc2026/models/egm_to_lambdas \
  --cov=src/wc2026/evaluation/clv_pipeline \
  --cov-report=term-missing \
  --cov-fail-under=70 \
  --no-header -q 2>&1
echo "=== Critical module coverage: PASSED ==="

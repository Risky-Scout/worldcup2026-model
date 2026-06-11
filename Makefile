PYTHON       := /opt/homebrew/bin/python3.10
PIP          := $(PYTHON) -m pip
WC2026       := $(PYTHON) -m wc2026.cli
PYTEST       := $(PYTHON) -m pytest
RUFF         := $(PYTHON) -m ruff
MYPY         := $(PYTHON) -m mypy
DATE         ?= $(shell date +%Y-%m-%d)
HOME_TEAM    ?= Brazil
AWAY_TEAM    ?= France
SEASON       ?= 2026
DATA_VERSION ?= v1

.PHONY: help install install-dev test lint typecheck \
        fetch-bdl build-dataset train backtest calibrate \
        predict-date predict-match publish-today audit \
        validate-published validate-live \
        clean all

##@@ Help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make \033[36m<target>\033[0m\n\n"} /^##@@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@@ Setup
install: ## Install production dependencies
	$(PIP) install -e ".[dev]"

install-dev: install ## Install with dev extras

##@@ Quality
test: ## Run all tests with coverage
	$(PYTEST) tests/ -v --tb=short --cov=wc2026 --cov-report=term-missing

lint: ## Run ruff linter
	$(RUFF) check src/ tests/

typecheck: ## Run mypy type checker
	$(MYPY) src/wc2026/

format: ## Auto-format with ruff
	$(RUFF) format src/ tests/

##@@ Data
fetch-bdl: ## Fetch and snapshot all BDL World Cup data
	$(WC2026) fetch-bdl --seasons 2018,2022,2026

build-dataset: ## Build versioned parquet tables from raw BDL snapshots
	$(WC2026) build-dataset --seasons 2018,2022,2026 --data-version $(DATA_VERSION)

##@@ Models
train: ## Fit model ladder on all completed matches
	$(WC2026) train --data-version $(DATA_VERSION)

backtest: ## Walk-forward OOF backtest for all models
	$(WC2026) backtest --data-version $(DATA_VERSION)

calibrate: ## Fit temperature scaling on OOF predictions
	$(WC2026) calibrate --data-version $(DATA_VERSION)

##@@ Predictions
predict-date: ## Predict all matches on DATE (default: today)
	$(WC2026) predict-date --date $(DATE) --season $(SEASON) --data-version $(DATA_VERSION)

predict-match: ## Predict HOME vs AWAY match
	$(WC2026) predict-match --home "$(HOME_TEAM)" --away "$(AWAY_TEAM)" --season $(SEASON)

predict-all-scheduled: ## Predict all scheduled 2026 matches
	$(WC2026) predict-all-scheduled --season $(SEASON) --data-version $(DATA_VERSION)

publish-today: ## Write today's predictions to data/published/
	$(WC2026) publish-today --season $(SEASON) --data-version $(DATA_VERSION)

##@@ Quality / Audit
audit: ## Run consistency and quality checks
	$(WC2026) audit --data-version $(DATA_VERSION)

validate-published: ## Validate all committed published JSON artifacts for PMF integrity
	@echo "Running artifact validation tests against data/published/*.json ..."
	$(PYTEST) tests/test_published_json.py -v --tb=short --no-cov \
	    -k "TestPublishedMatchPMF" \
	    && echo "✓ All published artifact tests PASSED" \
	    || (echo "✗ ARTIFACT VALIDATION FAILED — published JSON has integrity violations" && exit 1)

validate-live: ## Validate live replay (stub — live engine not yet implemented)
	@echo "Live replay validation: NOT YET IMPLEMENTED"
	@echo "Required: src/wc2026/live/ modules and data/predictions/live_replay_2022.parquet"
	@exit 1

##@@ Cleanup
clean: ## Remove compiled files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

clean-data: ## Remove all processed data (keeps raw snapshots)
	rm -rf data/processed/ data/predictions/ data/published/

##@@ Meta
all: install test lint ## Install, test, and lint

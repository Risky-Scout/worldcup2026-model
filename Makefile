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
        pipeline update post-match clv-close clv-summary \
        docker-build docker-run \
        clean clean-data all

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

predict-match: ## Predict HOME_TEAM vs AWAY_TEAM (use HOME_TEAM=X AWAY_TEAM=Y, not HOME=)
	$(WC2026) predict-match --home "$(HOME_TEAM)" --away "$(AWAY_TEAM)" --season $(SEASON)

predict-all-scheduled: ## Predict all scheduled 2026 matches
	$(WC2026) predict-all-scheduled --season $(SEASON) --data-version $(DATA_VERSION)

publish-today: ## Write today's predictions to data/published/
	$(WC2026) publish-today --season $(SEASON) --data-version $(DATA_VERSION)

##@@ Daily operations (run these after each matchday)
pipeline: ## Run the full prediction pipeline (fetch → build → predict → validate)
	$(PYTHON) scripts/run_real_pipeline.py

update: ## Daily update: fetch latest BDL data → rebuild → re-predict → validate
	$(PYTHON) scripts/daily_update.py --date $(DATE)

post-match: ## Post-match update for a completed date (record CLV outcomes, update ratings)
	$(PYTHON) scripts/daily_update.py --date $(DATE) --post-match

clv-close: ## Record closing lines in CLV store for matches kicking off today
	$(PYTHON) scripts/clv_ops.py close --date $(DATE)

clv-summary: ## Print current CLV summary report
	$(PYTHON) scripts/clv_ops.py summary

simulate: ## Monte Carlo group stage advancement probabilities (50k sims, saves report)
	$(WC2026) simulate --n 50000 --save

simulate-group: ## Simulate one group: make simulate-group GROUP="Group A"
	$(WC2026) simulate --n 50000 --group "$(GROUP)"

winner: ## Tournament winner probabilities via full bracket simulation (20k sims)
	$(WC2026) simulate --winner --n 20000 --save

report: ## Generate matchday briefing report for DATE (default: today)
	$(PYTHON) scripts/matchday_report.py --date $(DATE)

upload: ## Upload predictions JSON to sportsodds.wizardofodds.com via FTP
	$(PYTHON) scripts/upload_predictions.py --date $(DATE)

deploy: ## Upload HTML page and predictions JSON to production server
	$(PYTHON) scripts/upload_predictions.py --date $(DATE)
	$(PYTHON) scripts/deploy_html.py

live-snapshot: ## Run live match PMF snapshot and upload wc-live.json to FTP
	$(PYTHON) scripts/live_snapshot.py

deploy-live: ## Deploy live PMF page and run live snapshot
	$(PYTHON) scripts/deploy_html.py
	$(PYTHON) scripts/live_snapshot.py

##@@ Docker
docker-build: ## Build the Docker image
	docker build -t wc2026-pmf:latest .

docker-run: ## Run the pipeline in Docker (requires .env with BDL_API_KEY)
	docker run --rm -v $(PWD)/data:/app/data -v $(PWD)/reports:/app/reports \
	    --env-file .env wc2026-pmf:latest predict-date --date $(DATE)

##@@ Quality / Audit
audit: ## Run consistency and quality checks
	$(WC2026) audit --data-version $(DATA_VERSION)

validate-published: ## Validate all committed published JSON artifacts for PMF integrity
	@echo "Running artifact validation tests against data/published/*.json ..."
	$(PYTEST) tests/test_published_json.py -v --tb=short --no-cov \
	    -k "TestPublishedMatchPMF" \
	    && echo "✓ All published artifact tests PASSED" \
	    || (echo "✗ ARTIFACT VALIDATION FAILED — published JSON has integrity violations" && exit 1)

validate-live: ## Validate live engine (smoke-tests + replay parquet if present)
	@echo "Running live engine smoke tests..."
	$(PYTEST) tests/test_live.py -v --tb=short --no-cov \
	    && echo "✓ Live engine tests PASSED" \
	    || (echo "✗ Live engine tests FAILED" && exit 1)
	@if [ -f data/predictions/live_replay_2022.parquet ]; then \
	    echo "✓ live_replay_2022.parquet exists"; \
	    $(PYTHON) -c "import pandas as pd; df=pd.read_parquet('data/predictions/live_replay_2022.parquet'); print(f'Replay rows: {len(df)}, matches: {df.match_id.nunique()}')"; \
	else \
	    echo "⚠ live_replay_2022.parquet missing — run: make fetch-bdl && python scripts/run_real_pipeline.py"; \
	fi

##@@ Cleanup
clean: ## Remove compiled files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

clean-data: ## Remove all processed data (keeps raw snapshots)
	rm -rf data/processed/ data/predictions/ data/published/

##@@ Meta
all: install test lint ## Install, test, and lint

.PHONY: help install test lint format type-check check run clean setup-features tck-report report-install report-generate report-clean rp-start rp-stop rp-open rp-install

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies using uv
	uv sync
	uv sync --group dev

test:  ## Run unit tests with pytest
	uv run pytest tests/ -v

run:  ## Run all feature tests with behave
	uv run behave

run-example:  ## Run example feature only
	uv run behave features/example.feature

run-verbose:  ## Run feature tests with verbose output
	uv run behave -v

run-tag:  ## Run feature tests with specific tag (usage: make run-tag TAG=@match)
	uv run behave --tags=$(TAG)

lint:  ## Lint code with ruff
	uv run ruff check .

format:  ## Format code with ruff
	uv run ruff format .

format-check:  ## Check code formatting without making changes
	uv run ruff format --check .

type-check:  ## Run type checking with mypy
	uv run mypy src/

check: lint format-check type-check  ## Run all code quality checks

fix:  ## Auto-fix linting issues
	uv run ruff check --fix .

setup-features:  ## Copy feature files from openCypher TCK (usage: make setup-features TCK=../tck/features)
	python setup_features.py $(TCK)

# ── HTML Report Pipeline ──────────────────────────────────────────────
report-install:  ## Install Node.js report generator dependencies
	npm install --prefix .

tck-report:  ## Run TCK tests with progress bar, stream to ReportPortal
	@mkdir -p results
	-behave features/ --no-capture \
		-f json -o results/$$(date +%Y%m%d-%H%M%S).json \
		-f progress3 --summary

tck-report-verbose:  ## Same as tck-report but with full pretty output
	@mkdir -p results
	-behave features/ --no-capture \
		-f json -o results/$$(date +%Y%m%d-%H%M%S).json \
		-f pretty

tck-report-full:  ## Rebuild raphtory from source, then run TCK tests + reports
	$(MAKE) -C ../.. install-python
	$(MAKE) tck-report

tck-golden:  ## Snapshot the latest result as the golden baseline
	@latest=$$(ls -t results/*.json 2>/dev/null | grep -v golden | head -1); \
	if [ -z "$$latest" ]; then echo "No result files found. Run make tck-report first."; exit 1; fi; \
	cp "$$latest" results/golden.json && echo "✅ Golden baseline set from $$latest"

tck-diff:  ## Show regressions vs golden baseline (or between two most recent runs)
	python3 diff-results.py

report-generate:  ## Generate HTML report from existing results (no test run)
	node generate-report.js

report-clean:  ## Remove all result JSON files and generated reports
	rm -rf results/ report/

# ── ReportPortal Server ───────────────────────────────────────────────
rp-install:  ## Install the ReportPortal Behave agent into the active Python environment
	pip install behave-reportportal

rp-start:  ## Start the ReportPortal Docker stack (UI at http://localhost:8080)
	docker compose -f docker-compose.rp.yml -p reportportal up -d
	@echo ""
	@echo "  ReportPortal starting... wait ~60s then open http://localhost:8080"
	@echo "  Login: superadmin / erebus"
	@echo "  First run: create project 'raphtory_tck', generate API key,"
	@echo "  then paste it into features/behave.ini under [report_portal] api_key"

rp-stop:  ## Stop the ReportPortal Docker stack (data is preserved in Docker volumes)
	docker compose -f docker-compose.rp.yml -p reportportal down

rp-open:  ## Open the ReportPortal UI in your browser
	open http://localhost:8080/ui/

clean:  ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

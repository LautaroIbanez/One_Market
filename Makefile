# One Market - Makefile

.PHONY: help install install-dev test test-cov test-fast lint format clean setup run-api run-ui run-all health

help:
	@echo "=========================================="
	@echo "One Market - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install dependencies"
	@echo "  make install-dev  - Install with dev dependencies"
	@echo "  make setup        - Full setup (install + create dirs)"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make test-fast    - Run tests without slow ones"
	@echo "  make health       - Run health check"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run linters (ruff + mypy)"
	@echo "  make format       - Format code (black + ruff)"
	@echo "  make check        - Lint + test"
	@echo ""
	@echo "Running:"
	@echo "  make run-api      - Run FastAPI server"
	@echo "  make run-ui       - Run Streamlit dashboard"
	@echo "  make run-all      - Run API + UI (requires tmux or manual)"
	@echo "  make demos        - Run all demo scripts"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Clean cache files"
	@echo "  make clean-all    - Clean cache + logs + storage"
	@echo ""

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest-cov pytest-asyncio black mypy ruff ipython jupyter

setup:
	@echo "Setting up One Market..."
	pip install -r requirements.txt
	python scripts/setup.py
	@echo "Setup complete!"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80

test-fast:
	pytest tests/ -v -m "not slow"

health:
	python scripts/health_check.py

lint:
	ruff check app/ tests/ main.py
	@echo "Linting complete!"

format:
	black app/ tests/ examples/ main.py
	ruff check --fix app/ tests/ main.py
	@echo "Formatting complete!"

check: lint test
	@echo "All checks passed!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "Cleanup complete!"

clean-all: clean
	rm -rf logs/*.log 2>/dev/null || true
	@echo "Full cleanup complete!"

run-api:
	python main.py

run-ui:
	streamlit run ui/app.py

run-all:
	@echo "Run in separate terminals:"
	@echo "  Terminal 1: make run-api"
	@echo "  Terminal 2: make run-ui"

demos:
	python examples/example_core_usage.py
	python examples/example_research_signals.py
	python examples/example_backtest_complete.py
	python examples/example_daily_decision.py

.DEFAULT_GOAL := help


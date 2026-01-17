# Noah Reading Agent - Python Backend Makefile

.PHONY: help install dev test lint format clean build docker

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with uv
	uv sync

dev: ## Start development server
	uv run python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=html --cov-report=term

lint: ## Run linting
	uv run ruff check src/
	uv run mypy src/

format: ## Format code
	uv run black src/
	uv run isort src/
	uv run ruff format src/

clean: ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

build: ## Build the package
	uv build

docker-build: ## Build Docker image
	docker build -t noah-reading-agent-backend .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env noah-reading-agent-backend

setup: ## Run initial setup
	python setup.py

# Development workflow
check: lint test ## Run all checks (lint + test)

ci: install check ## Run CI pipeline (install + check)

# Database commands
db-upgrade: ## Run database migrations
	uv run alembic upgrade head

db-downgrade: ## Rollback database migration
	uv run alembic downgrade -1

db-revision: ## Create new database migration
	uv run alembic revision --autogenerate -m "$(msg)"
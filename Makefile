.PHONY: help install dev test lint fmt typecheck check migrate migration seed docker-build docker-up docker-down deploy clean

help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies with uv"
	@echo "  dev          - Run dev server with reload"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Lint with ruff"
	@echo "  fmt          - Format with ruff"
	@echo "  typecheck    - Type check with mypy"
	@echo "  check        - Run lint + typecheck + test"
	@echo "  migrate      - Apply Alembic migrations"
	@echo "  migration    - Create new migration (usage: make migration m='add users')"
	@echo "  seed         - Populate DB with classic books (requires OPENROUTER_API_KEY)"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up    - Start docker-compose"
	@echo "  docker-down  - Stop docker-compose"
	@echo "  deploy       - Deploy to Fly.io"
	@echo "  clean        - Remove caches and build artifacts"

install:
	uv sync --all-extras

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy app

check: lint typecheck test

migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision --autogenerate -m "$(m)"

seed:
	uv run python scripts/seed.py

docker-build:
	docker build -t virtual-library-api:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

deploy:
	flyctl deploy --remote-only --build-arg GIT_SHA=$$(git rev-parse HEAD)

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage build dist
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

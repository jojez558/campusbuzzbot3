# ═══════════════════════════════════════════════════════════
#  CampusBuzz Kenya — Developer Makefile
# ═══════════════════════════════════════════════════════════

.PHONY: help install run docker-up docker-down docker-logs \
        migrate migrate-new lint format test clean

help:
	@echo ""
	@echo "  CampusBuzz Kenya — Available Commands"
	@echo "  ────────────────────────────────────────"
	@echo "  make install       Install Python dependencies"
	@echo "  make run           Run bot in polling mode (dev)"
	@echo "  make docker-up     Start full stack (bot+db+redis)"
	@echo "  make docker-down   Stop all containers"
	@echo "  make docker-logs   Tail bot logs"
	@echo "  make migrate       Run Alembic migrations"
	@echo "  make migrate-new m=<message>  Create new migration"
	@echo "  make lint          Run flake8 linter"
	@echo "  make format        Run black formatter"
	@echo "  make health        Run link health check manually"
	@echo "  make clean         Remove __pycache__ etc."
	@echo ""

install:
	pip install -r requirements.txt

run:
	python main.py

docker-up:
	docker compose up -d --build
	@echo "✅ CampusBuzz stack is running"
	@echo "   Bot logs: make docker-logs"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f bot

docker-rebuild:
	docker compose down
	docker compose up -d --build --force-recreate

migrate:
	alembic upgrade head

migrate-new:
	alembic revision --autogenerate -m "$(m)"

lint:
	flake8 . --max-line-length=100 --exclude=venv,.venv,alembic

format:
	black . --line-length=100 --exclude="/(venv|\.venv|alembic)/"

health:
	python -m utils.link_monitor

test:
	pytest tests/ -v --tb=short

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "🧹 Cleaned up"

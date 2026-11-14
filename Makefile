# ==============================================================================
# Development Automation Makefile
# ==============================================================================

.PHONY: help up down restart logs ps infra-up infra-down backend frontend test clean

help:
	@echo "Available commands:"
	@echo "  make up          Start all Docker services in background"
	@echo "  make down        Stop all Docker services"
	@echo "  make infra-up    Start only Postgres, Redis, and Ollama"
	@echo "  make infra-down  Stop infrastructure containers"
	@echo "  make logs        Tail Docker logs"
	@echo "  make ps          View status of Docker containers"
	@echo "  make backend     Run FastAPI backend locally"
	@echo "  make frontend    Run React Vite frontend locally"
	@echo "  make test        Run backend and frontend tests"
	@echo "  make clean       Clean temporary cache files"

up:
	docker-compose up -d --build

down:
	docker-compose down

infra-up:
	docker-compose up -d postgres redis ollama

infra-down:
	docker-compose stop postgres redis ollama

restart:
	docker-compose restart

logs:
	docker-compose logs -f

ps:
	docker-compose ps

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest
	cd frontend && npm run test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

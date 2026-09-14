.PHONY: help install install-backend install-frontend test test-backend test-frontend \
        check lint build dev dev-backend dev-frontend

# Default target
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install          Install dependencies for both backend and frontend"
	@echo "  install-backend  Install backend dependencies using uv"
	@echo "  install-frontend Install frontend dependencies using npm"
	@echo "  test             Run all tests (backend + frontend)"
	@echo "  test-backend     Run backend tests (uv run pytest)"
	@echo "  test-frontend    Run frontend tests (npm test)"
	@echo "  check            Run full validation: linting, tests, and frontend build"
	@echo "  lint             Run linters for frontend"
	@echo "  build            Build frontend production bundle"
	@echo "  dev              Run backend and frontend concurrently in development mode"
	@echo "  dev-backend      Run FastAPI server with reload on port 8000"
	@echo "  dev-frontend     Run Vite dev server on port 5173"

# Installation
install: install-backend install-frontend

install-backend:
	cd backend && uv sync

install-frontend:
	cd frontend && npm install

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest

test-frontend:
	cd frontend && npm test

# Linting & Checking
lint:
	cd frontend && npm run lint

build:
	cd frontend && npm run build

check: test-backend test-frontend lint build
	@echo "\nAll backend & frontend checks passed successfully!"

# Development Servers
dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --reload-dir app --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend and frontend concurrently (Ctrl+C to stop)..."
	@make -j 2 dev-backend dev-frontend

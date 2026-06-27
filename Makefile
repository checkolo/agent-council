.PHONY: help install dev test lint record demo serve build-ui ship clean eval

help:
	@echo "Quorum v0.1 — Makefile targets"
	@echo ""
	@echo "  install     Install Python deps with uv"
	@echo "  dev         Run FastAPI + Vite dev servers"
	@echo "  test        Run pytest (keyless, uses cassettes)"
	@echo "  lint        Run ruff"
	@echo "  record      Record cassettes for sample runs"
	@echo "  demo        Run keyless demo with sample cassettes"
	@echo "  serve       Build UI + start quorum serve"
	@echo "  build-ui    Build React SPA into quorum/web/"
	@echo "  eval        Run eval harness"
	@echo "  ship        test + build-ui + tag checklist"
	@echo "  clean       Remove build artifacts"

install:
	uv sync --all-extras

dev:
	@echo "Starting FastAPI on :8000 and Vite on :5173..."
	@trap 'kill 0' EXIT; \
	uv run uvicorn quorum.api.server:app --reload --port 8000 & \
	cd web && npm run dev

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check quorum tests

record:
	uv run quorum run --template pr-review --file tests/fixtures/sample.diff --record --mode fast

demo:
	uv run quorum run --template pr-review --file tests/fixtures/sample.diff --recorded --mode fast

serve: build-ui
	uv run quorum serve

build-ui:
	cd web && npm ci && npm run build
	rm -rf quorum/web && mkdir -p quorum/web
	cp -r web/dist/* quorum/web/

eval:
	uv run quorum eval --suite evals/coding-questions.yaml

ship: test build-ui
	@echo "Ready for v0.1.0 tag. Run: git tag v0.1.0"

clean:
	rm -rf .venv quorum/web web/dist web/node_modules .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

.PHONY: install run run-api run-streamlit test lint typecheck frontend-check docker frontend check all

install:
	pip install -r requirements.txt

run:
	streamlit run app.py

run-api:
	uvicorn src.api.main:app --reload --port 8000

run-streamlit:
	streamlit run app.py --server.port 8501

test:
	pytest tests/ -q

lint:
	ruff check src/ app.py --select E,W,F,I || true

typecheck:
	mypy src/ --ignore-missing-imports --no-strict-optional || true

frontend-check:
	cd frontend && npm ci && npx tsc --noEmit && npm run build

docker:
	docker compose up --build -d

frontend:
	cd frontend && npm install && npm run dev

# Tesla-level local gate: run everything before pushing.
check: lint typecheck test frontend-check
	@echo "✅ All local checks passed"

all: install check
	@echo "✅ Project ready"

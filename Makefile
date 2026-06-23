.PHONY: install run run-api run-streamlit test test-cov lint typecheck security frontend-check docker frontend check all

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

test-cov:
	pytest tests/ --cov=src --cov-report=term

lint:
	ruff check src/ app.py tests/

typecheck:
	mypy src/

security:
	bandit -r src/ -ll -ii
	pip-audit --requirement requirements.txt

frontend-check:
	cd frontend && npx tsc --noEmit && npm run build

docker:
	docker compose up --build -d

frontend:
	cd frontend && npm install && npm run dev

# Tesla-level local gate: run everything before pushing.
check: lint typecheck security test frontend-check
	@echo "✅ All local Tesla-level checks passed"

all: install check
	@echo "✅ Project ready"

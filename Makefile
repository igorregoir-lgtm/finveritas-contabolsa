.PHONY: install run run-api run-streamlit test docker frontend

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

docker:
	docker compose up --build -d

frontend:
	cd frontend && npm install && npm run dev

all: install test docker
	@echo "✅ All systems ready"

install:
	pip install -e ".[dev]"
test:
	pytest tests/ -v --cov=src --cov-fail-under=70
lint:
	ruff check src/ tests/
run-api:
	uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
run-frontend:
	cd frontend && npm run dev
run-demo:
	python demo_full_system.py
docker-build:
	docker build -t sattrade:latest .

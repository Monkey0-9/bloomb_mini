.PHONY: install test lint security docker-build run-demo run-api run-frontend run-all clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=80

lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports --strict

security:
	pip-audit
	bandit -r src/ -ll

docker-build:
	docker build -t sattrade:latest .
	docker run --rm sattrade:latest pytest tests/ -v

run-demo:
	python demo_full_system.py

run-api:
	uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

run-all:
	make run-api &
	make run-frontend

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	find . -name ".coverage" -delete 2>/dev/null; true

.PHONY: test install run clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

run:
	python -m src.api.server

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.PHONY: check lint test fmt

check: lint test

lint:
	ruff check src tests pipeline benchmark

test:
	python3 -m pytest

fmt:
	ruff fmt src tests
	ruff check --fix src tests

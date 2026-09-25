.PHONY: setup check lint test fmt

setup:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

check: lint test

lint:
	ruff check src tests pipeline benchmark

test:
	python3 -m pytest

fmt:
	ruff fmt src tests
	ruff check --fix src tests

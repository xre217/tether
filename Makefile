.PHONY: install dev test lint clean run help

help:
	@echo "Tether development commands:"
	@echo "  make install     - Install the package in editable mode"
	@echo "  make dev         - Install dev dependencies + pre-commit"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run ruff + mypy"
	@echo "  make run         - Run tether --help (requires uv or venv)"

install:
	uv pip install -e ".[dev]"

dev:
	uv pip install -e ".[dev,ollama]"
	pre-commit install

test:
	pytest -v

lint:
	ruff check src tests
	mypy src

clean:
	rm -rf build dist *.egg-info .venv .pytest_cache .mypy_cache .ruff_cache

run:
	uv run tether --help

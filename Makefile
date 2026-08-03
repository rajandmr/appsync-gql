.PHONY: lint typecheck check install

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy utils functions

check: lint typecheck
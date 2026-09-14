.PHONY: quality test build release-check

quality:
	python -m ruff check src tests
	python -m mypy src

test:
	python -m pytest -q

build:
	python -m build --no-isolation

release-check: quality test build

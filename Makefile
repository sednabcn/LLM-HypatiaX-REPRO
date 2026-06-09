.PHONY: test lint

test:
	python -m pytest tests/

lint:
	python -m flake8 scripts/ utils/

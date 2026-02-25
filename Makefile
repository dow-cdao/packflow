.PHONY: install dev test

install:
	poetry install

dev:
	poetry install --all-groups

test: dev
	pytest --cov=src --cov-report=html:tests/calc_cov
	open tests/calc_cov/index.html

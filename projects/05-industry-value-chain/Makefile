# Project 5 — Industry Value-Chain
# Override the interpreter, e.g.  make build PYTHON=~/.ctf-tools/venv/bin/python
PYTHON ?= python3

.PHONY: help ingest build export analysis test pipeline clean

help:
	@echo "make ingest    - download the 6 core Damodaran .xls files (cache + hash)"
	@echo "make build     - parse + resolve industries + build warehouse.duckdb"
	@echo "make export    - emit sql/postgres/*.sql (+ csv) for Supabase"
	@echo "make analysis  - compute the rank-reversal + market-pricing headline"
	@echo "make test      - run pytest quality/parse/crosswalk/analysis gates"
	@echo "make pipeline  - ingest -> build -> export -> analysis"

ingest:
	$(PYTHON) -m src.ingest

build:
	$(PYTHON) -m src.warehouse

export:
	$(PYTHON) -m src.export_postgres

analysis:
	$(PYTHON) -m src.analysis

test:
	$(PYTHON) -m pytest

pipeline: ingest build export analysis

clean:
	rm -f warehouse.duckdb
	rm -rf sql/postgres/*.sql sql/postgres/csv

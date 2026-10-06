.PHONY: install test lint run eval

install:
	python -m pip install -e ".[dev,ai]"

test:
	pytest -q

lint:
	ruff check .

run:
	uvicorn procurement_agent.api:app --reload

eval:
	PYTHONPATH=src python evals/run_policy_evals.py

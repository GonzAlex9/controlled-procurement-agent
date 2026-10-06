.PHONY: install test lint run eval eval-policy eval-agent eval-agent-ai

install:
	python -m pip install -e ".[dev,ai]"

test:
	pytest -q

lint:
	ruff check .

run:
	uvicorn procurement_agent.api:app --reload

eval: eval-policy eval-agent

eval-policy:
	PYTHONPATH=src python evals/run_policy_evals.py

eval-agent:
	PYTHONPATH=src python evals/run_agent_evals.py --mode deterministic

eval-agent-ai:
	PYTHONPATH=src python evals/run_agent_evals.py --mode openai

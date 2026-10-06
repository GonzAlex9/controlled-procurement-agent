.PHONY: install test lint run eval eval-policy eval-agent eval-agent-ai eval-security eval-security-ai

install:
	python -m pip install -e ".[dev,ai]"

test:
	pytest -q

lint:
	ruff check .

run:
	uvicorn procurement_agent.api:app --reload

eval: eval-policy eval-agent eval-security

eval-policy:
	PYTHONPATH=src python evals/run_policy_evals.py

eval-agent:
	PYTHONPATH=src python evals/run_agent_evals.py --mode deterministic

eval-agent-ai:
	PYTHONPATH=src python evals/run_agent_evals.py --mode openai

eval-security:
	PYTHONPATH=src python evals/run_security_evals.py --mode deterministic

eval-security-ai:
	PYTHONPATH=src python evals/run_security_evals.py --mode openai

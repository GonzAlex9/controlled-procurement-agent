.PHONY: install test lint run mcp-run mcp-http eval eval-policy eval-agent eval-agent-ai eval-security eval-security-ai

install:
	python -m pip install -e ".[dev,ai,observability,mcp,postgres]"

test:
	pytest -q

lint:
	ruff check .

run:
	uvicorn procurement_agent.api:app --reload

mcp-run:
	python -m procurement_agent.mcp_server

mcp-http:
	MCP_TRANSPORT=streamable-http python -m procurement_agent.mcp_server

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

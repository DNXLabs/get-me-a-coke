.PHONY: install dev test lint type-check format api agent deploy destroy synth

# Setup
install:
	uv sync

# Development
dev:
	uv run uvicorn vending_machine.app:app --reload --port 8000

wallet:
	uv run uvicorn wallet_service.app:app --reload --port 8001

agent:
	AWS_PROFILE=nonprod-dnxai STRANDS_HTTP_ALLOW_INSECURE_SSL=true uv run python -m agent.cli --interactive

agent-buy:
	AWS_PROFILE=nonprod-dnxai STRANDS_HTTP_ALLOW_INSECURE_SSL=true uv run python -m agent.cli "Buy me a coke"

# Quality
lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

type-check:
	uv run mypy src/

# Testing
test:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v -m integration

test-all:
	uv run pytest -v

# Infrastructure
synth:
	cd infra && pip install -r requirements.txt && cdk synth

deploy:
	cd infra && cdk deploy --all --profile nonprod-dnxai --require-approval never

destroy:
	cd infra && cdk destroy --all --profile nonprod-dnxai --force

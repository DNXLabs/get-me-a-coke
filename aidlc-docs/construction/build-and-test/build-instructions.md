# Build Instructions

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- AWS CLI configured with profile `nonprod-dnxai`

## Install Dependencies

```bash
# From project root
uv sync
```

This installs all dependencies from `pyproject.toml` including dev dependencies.

## Verify Installation

```bash
# Check Python version
uv run python --version

# Verify imports work
uv run python -c "from vending_machine.app import app; print('Vending Machine OK')"
uv run python -c "from agent.config import AgentConfig; print('Agent OK')"
uv run python -c "from observability.exporters import build_grafana_auth_headers; print('Observability OK')"
```

## Run Vending Machine Locally

```bash
uv run uvicorn vending_machine.app:app --reload --port 8000
```

Verify: `curl http://localhost:8000/products`

## Run Agent (requires .env configured)

```bash
# Single-shot
uv run python -m agent.cli "Buy me a coke"

# Interactive
uv run python -m agent.cli --interactive
```

## Build CDK Infrastructure

```bash
cd infra
pip install -r requirements.txt
cdk synth
```

## Code Quality

```bash
# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run mypy src/
```

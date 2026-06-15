# Unit Test Instructions

## Run All Unit Tests

```bash
uv run pytest tests/unit/ -v
```

## Run Tests by Component

```bash
# Vending Machine tests
uv run pytest tests/unit/test_vending_machine/ -v

# Agent tests
uv run pytest tests/unit/test_agent/ -v

# Observability tests
uv run pytest tests/unit/test_observability/ -v
```

## Run with Coverage

```bash
uv run pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html
```

Coverage report will be generated in `htmlcov/`.

## Test Categories

### Vending Machine (tests/unit/test_vending_machine/)
- `test_models.py` — Product catalog, model serialization
- `test_x402.py` — Payment validation logic
- `test_routes.py` — API endpoint behavior (402 flow, 404, 200)

### Agent (tests/unit/test_agent/)
- `test_config.py` — Configuration loading, property checks
- `test_agent.py` — System prompt generation
- `test_cli.py` — CLI argument parsing, mode dispatch

### Observability (tests/unit/test_observability/)
- `test_telemetry.py` — Auth header building, endpoint construction, graceful degradation

## Expected Results

All unit tests should pass without any external dependencies (no AWS, no Bedrock, no Grafana). They use:
- FastAPI TestClient for API tests
- unittest.mock for external service mocking
- No network calls required

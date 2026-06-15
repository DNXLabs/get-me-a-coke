# Integration Test Instructions

## Prerequisites

- Unit tests passing
- AWS credentials configured (`AWS_PROFILE=nonprod-dnxai`)
- `.env` file with valid Bedrock access (for real model calls)

## Run Integration Tests

```bash
uv run pytest tests/integration/ -v -m integration
```

## Test Scenarios

### test_vending_machine_catalog_accessible
- Verifies the vending machine catalog endpoint returns valid products
- Uses FastAPI TestClient (no network required)

### test_vending_machine_402_flow
- Verifies the full x402 payment flow:
  1. POST without payment → 402 with terms
  2. POST with payment header → 200 dispensed
- Uses FastAPI TestClient (no network required)

### test_agent_autonomous_purchase (commented out — expensive)
- Full end-to-end: agent calls real Bedrock (Nemotron Nano) + local vending machine
- Requires: AWS credentials, Bedrock model access
- Cost: ~$0.001 per run (model inference)
- Uncomment when ready for full integration testing

## Running with Real Bedrock

To enable the full agent integration test:
1. Ensure `AWS_PROFILE=nonprod-dnxai` has Bedrock access
2. Uncomment `test_agent_autonomous_purchase` in `tests/integration/test_agent_vending_machine.py`
3. Run: `uv run pytest tests/integration/ -v -m integration -m slow`

## Mocking Strategy

| Component | Unit Tests | Integration Tests |
|-----------|-----------|-------------------|
| Vending Machine API | TestClient (real) | TestClient (real) |
| Bedrock (model) | Mocked | Real (Nemotron Nano) |
| AgentCore Payments | Mocked | Mocked |
| Grafana OTLP | Not tested | Not tested (best-effort) |

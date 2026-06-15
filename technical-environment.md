# Technical Environment: Get Me a Coke

## Language and Package Manager

- **Python 3.12+**
- **uv** for all package management
- `pyproject.toml` for project configuration
- `uv.lock` committed to Git

## Frameworks

| Component | Framework | Purpose |
|-----------|-----------|---------|
| Vending Machine API | FastAPI + Mangum | x402-compatible HTTP API on Lambda |
| Agent | Strands Agents SDK | Model-driven agent with tool loop |
| Agent Payments | AgentCore Payments (Strands plugin) | Managed x402 payment handling |
| Observability | OpenInference + OpenTelemetry | AI tracing and spans |

## Cloud and Deployment

- **AWS**, profile `nonprod-dnxai` (admin), **ap-southeast-2** (Sydney)
- **Amazon Bedrock AgentCore Runtime** for the agent (managed, serverless, built-in observability)
- **AWS Lambda** for the vending machine API (via Mangum)
- **API Gateway** (HTTP API) in front of the vending machine Lambda
- Local dev: `uvicorn` for API, CLI script for agent
- Infrastructure: **AgentCore CLI** (`agentcore configure` → `agentcore launch`) or **AWS CDK**

### Why AgentCore Runtime for the Agent

- Managed container deployment (no manual Docker/Lambda config)
- Built-in observability (CloudWatch + ADOT)
- Native payments plugin integration
- Scales automatically
- Works directly with Strands Agents SDK

## Payments Architecture

### Agent Side (Buyer) — AgentCore Payments Plugin

AgentCore payments handles the full x402 flow automatically:
- Wallet management (Coinbase CDP or Stripe Privy credentials)
- Automatic 402 detection and payment execution
- Spending limits and session controls
- Audit trail

Dependencies: `pip install bedrock-agentcore[strands-agents]`

### Vending Machine Side (Seller) — x402 Server

The vending machine API implements x402 server behavior:
1. Returns `HTTP 402` with payment terms (price, wallet address, network) when unpaid
2. Validates payment proof header on retry
3. Dispenses "coke" on valid payment

For MVP: mock payment validation (accept any well-formed payment header).
For Phase 2: real on-chain validation via Coinbase SDK.

### Prerequisites for AgentCore Payments

1. Coinbase CDP credentials (or Stripe Privy) stored in AgentCore Identity
2. Payment Manager + Connector created
3. Payment Instrument (embedded wallet) provisioned
4. Wallet funded (testnet USDC for dev)

## Testing

- **pytest** with pytest-cov
- **mypy** strict mode
- **ruff** for linting and formatting
- **moto** for mocking AWS services
- Local integration: run vending machine locally, agent calls it with mocked payment

## Do NOT Use

| Prohibited | Reason | Use Instead |
|-----------|--------|-------------|
| LangChain, LangGraph | Project uses Strands Agents SDK | Strands Agents SDK |
| Flask, Django | Project uses FastAPI | FastAPI |
| pip, poetry, pipenv | Project uses uv | uv |
| black, flake8, isort | Replaced by ruff | ruff |
| requests | Blocks async | httpx |
| Custom x402 agent implementation | AgentCore handles it | AgentCore Payments plugin |

## Security Basics

- **PoC** — no production hardening
- Agent wallet: testnet USDC via AgentCore payment instrument
- Spending limits enforced via AgentCore payment sessions
- Vending machine: x402 payment header validation
- TLS via API Gateway (default)
- IAM roles for AgentCore Runtime execution

## Observability

All telemetry goes to **Grafana** (Cloud or self-hosted). Single pane of glass.

- **Traces**: Strands agent spans + OpenInference AI semantics → Grafana Tempo
- **Metrics**: OTel metrics (token usage, latency, payment amounts) → Grafana Mimir/Prometheus
- **Logs**: Structured agent logs → Grafana Loki

### Stack

| Signal | Exporter | Grafana Backend |
|--------|----------|-----------------|
| Traces | OTLP | Tempo |
| Metrics | OTLP | Mimir |
| Logs | OTLP | Loki |

### Dependencies

```
openinference-instrumentation-strands-agents
opentelemetry-sdk
opentelemetry-exporter-otlp
```

### Wiring

Configuration loaded from `.env` file (see `.env.example` for required variables):

- `AWS_PROFILE` — AWS credentials profile
- `AWS_REGION` — deployment region
- `GRAFANA_OTLP_ENDPOINT` — Grafana Cloud OTLP gateway
- `GRAFANA_INSTANCE_ID` — Grafana stack instance ID
- `GRAFANA_API_TOKEN` — Grafana Cloud API token (scopes: traces:write, metrics:write, logs:write)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.strands import StrandsInstrumentor

# All signals → Grafana OTLP endpoint
GRAFANA_OTLP_ENDPOINT = "https://<your-stack>.grafana.net/otlp"
GRAFANA_AUTH = {"Authorization": "Basic <base64-instance-id:token>"}

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint=f"{GRAFANA_OTLP_ENDPOINT}/v1/traces", headers=GRAFANA_AUTH)
))
trace.set_tracer_provider(provider)

# Transforms Strands spans → OpenInference semantic conventions
StrandsInstrumentor().instrument()
```

AgentCore ADOT still runs (can't disable it), but Grafana is the primary observability destination. Ignore CloudWatch or use it as a backup.

## Project Structure

```
get-me-a-coke/
├── src/
│   ├── vending_machine/       # FastAPI app (x402 seller)
│   │   ├── app.py
│   │   ├── models.py
│   │   ├── x402.py            # x402 server-side payment handling
│   │   └── handler.py         # Lambda entry point (Mangum)
│   └── agent/                 # Strands agent (x402 buyer via AgentCore)
│       ├── agent.py           # Agent definition + tools + payments plugin
│       ├── tools/             # Agent tools
│       └── cli.py             # CLI entry point for local dev
├── tests/
├── infra/                     # CDK or agentcore config
├── aidlc-docs/                # AIDLC generated artifacts
├── vision.md
├── technical-environment.md
└── pyproject.toml
```

## Example Code Patterns

### Vending Machine — x402 Endpoint (Seller)

```python
from fastapi import APIRouter, Request, Response
from starlette.responses import JSONResponse

router = APIRouter()

PRODUCTS = {"coke": {"name": "Coke", "price_usd": "0.01", "wallet": "0x..."}}


@router.post("/purchase/{product_id}")
async def purchase(product_id: str, request: Request):
    payment_header = request.headers.get("X-PAYMENT")
    if not payment_header:
        # Return 402 with payment terms
        product = PRODUCTS[product_id]
        return JSONResponse(
            status_code=402,
            content={"price": product["price_usd"], "currency": "USDC", "network": "base-sepolia"},
            headers={"X-PAYMENT-REQUIRED": "true"},
        )
    # Validate payment (mock for MVP)
    return {"status": "dispensed", "product": product_id}
```

### Agent with AgentCore Payments (Buyer)

```python
from strands import Agent, tool
from strands_tools import http_request
from bedrock_agentcore.payments.integrations.config import AgentCorePaymentsPluginConfig
from bedrock_agentcore.payments.integrations.strands.plugin import AgentCorePaymentsPlugin

config = AgentCorePaymentsPluginConfig(
    payment_manager_arn="arn:aws:bedrock-agentcore:ap-southeast-2:...:payment-manager/...",
    user_id="thiago",
    payment_instrument_id="...",
    payment_session_id="...",
    region="ap-southeast-2",
)

plugin = AgentCorePaymentsPlugin(config)

agent = Agent(
    system_prompt="You buy cokes from vending machines. Use the HTTP tool to browse and purchase.",
    tools=[http_request],
    plugins=[plugin],
)

# Agent automatically handles 402 → pay → retry
agent("Buy me a coke from https://vending.example.com")
```

### Test

```python
import pytest
from fastapi.testclient import TestClient
from vending_machine.app import app

client = TestClient(app)


def test_no_payment_returns_402() -> None:
    response = client.post("/purchase/coke")
    assert response.status_code == 402


def test_valid_payment_dispenses() -> None:
    response = client.post("/purchase/coke", headers={"X-PAYMENT": "valid-proof"})
    assert response.status_code == 200
    assert response.json()["status"] == "dispensed"
```

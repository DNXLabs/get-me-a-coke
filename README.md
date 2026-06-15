# Get Me a Coke 🥤

Proof-of-concept: autonomous agent-to-service commerce using the x402 payment protocol.

An AI agent (Strands SDK + AgentCore Payments) autonomously discovers, pays for, and receives products from a vending machine API (FastAPI + x402).

## Quick Start

```bash
# Install dependencies
uv sync

# Run vending machine locally
make dev

# In another terminal — buy a coke
make agent-buy

# Or start interactive mode
make agent
```

## Architecture

```
AI Engineer → Agent CLI → Vending Machine API
                 ↓                    ↓
         AgentCore Payments     HTTP 402 + Payment Terms
                 ↓
         Grafana Cloud (Observability)
```

## Components

| Component | Location | Deployment |
|-----------|----------|------------|
| Vending Machine API | `src/vending_machine/` | Lambda + API Gateway |
| AI Agent | `src/agent/` | AgentCore Runtime |
| Observability | `src/observability/` | Embedded in agent |
| Infrastructure | `infra/` | CDK (CloudFormation) |

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required for local development:
- `AWS_PROFILE` / `AWS_REGION` — AWS credentials
- `VENDING_MACHINE_URL` — defaults to http://localhost:8000

Required for payments (AgentCore):
- `PAYMENT_MANAGER_ARN` — see [AgentCore Setup](docs/agentcore-setup.md)
- `PAYMENT_INSTRUMENT_ID`

Required for observability:
- `GRAFANA_OTLP_ENDPOINT` / `GRAFANA_INSTANCE_ID` / `GRAFANA_API_TOKEN`

## Development

```bash
make lint          # Run ruff linter
make format        # Auto-format code
make type-check    # Run mypy strict
make test          # Run unit tests
make test-all      # Run all tests (unit + integration)
```

## Deployment

```bash
make synth         # Validate CDK templates
make deploy        # Deploy all stacks to AWS
make destroy       # Tear down all resources
```

## Tech Stack

- Python 3.12+ / uv
- FastAPI + Mangum (vending machine)
- Strands Agents SDK + AgentCore Payments (agent)
- OpenTelemetry + OpenInference → Grafana Cloud (observability)
- AWS CDK (infrastructure)
- NVIDIA Nemotron Nano 3 30B via Bedrock (model)

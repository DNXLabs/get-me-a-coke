# Get Me a Coke 🥤

Proof-of-concept: autonomous agent-to-service commerce using the x402 payment protocol.

An AI agent (Strands Agents SDK on AWS Bedrock) autonomously discovers, pays for, and receives products from a vending machine API (FastAPI + x402), behind a human-in-the-loop approval gate — fully instrumented for AI observability with **OpenInference + Grafana Sigil → Grafana Cloud**.

## Demo & Resources

- 🎬 **Demo video:** [`docs/assets/get-me-a-coke.mp4`](docs/assets/get-me-a-coke.mp4) — end-to-end run of the agent buying a coke through the HITL approval gate.
- 📑 **Slide deck:** [`docs/assets/DNX-Grafana-AI-Observability-Get-me-a-coke.pdf`](docs/assets/DNX-Grafana-AI-Observability-Get-me-a-coke.pdf) — DNX × Grafana AI Observability walkthrough.

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
                            ┌─────────────────────────────────────────────┐
   AI Engineer ──prompt──▶  │  Agent CLI  (src/agent)                       │
                            │  Strands Agent + Bedrock (Nemotron Nano 3)    │
                            │                                               │
                            │  tools: list_products · get_purchase_quote    │
                            │         execute_purchase · wallet_pay/balance │
                            └───────┬───────────────────────────┬──────────┘
                                    │ httpx (W3C traceparent)    │
                       ┌────────────▼─────────┐      ┌───────────▼───────────┐
                       │ Vending Machine API  │      │  Wallet Service API   │
                       │ FastAPI + x402       │◀────▶│  FastAPI (X-API-Key)  │
                       │ HTTP 402 → terms     │      │  USDC pay / balance   │
                       └──────────────────────┘      └───────────────────────┘
                                    │
                       ┌────────────▼───────────────────────────────────────┐
                       │ HITL approval gate (Step Functions Activity)        │
                       │ execute_purchase blocks on human approve/reject     │
                       └─────────────────────────────────────────────────────┘

   Observability (every layer):  OpenInference spans + Sigil generations/tools
                                 ──── OTLP ────▶  Grafana Cloud (Tempo/Mimir/Loki)
                                 ──── Sigil ───▶  Grafana AI Observability
```

### Request flow

1. The agent lists products and fetches a **quote** (`get_purchase_quote`).
2. The user is shown the quote; the agent calls `execute_purchase`.
3. `execute_purchase` starts a **Step Functions** execution and blocks on a human `approve/reject` decision (the gate is a hard system-level control, not just a prompt instruction).
4. On approval, the agent pays via the **Wallet Service** (USDC) and receives an x402 payment proof, then redeems it at the **Vending Machine** to dispense the product.
5. Every step emits traces, metrics, logs (OpenInference → OTLP) and AI-native generation/tool records (Sigil).

## Components

| Component | Location | Deployment |
|-----------|----------|------------|
| AI Agent | `src/agent/` | AgentCore Runtime |
| Vending Machine API | `src/vending_machine/` | Lambda + API Gateway |
| Wallet Service API | `src/wallet_service/` | Lambda + API Gateway |
| Observability (OpenInference + Sigil) | `src/observability/` | Embedded in agent |
| Approval workflow (HITL) | `infra/stacks/approval_stack.py` | Step Functions |
| Infrastructure | `infra/` | CDK (CloudFormation) |

## Observability

The agent ships **three complementary layers** of telemetry, all landing in Grafana Cloud. They are wired in `src/observability/` and activated by `configure_telemetry(config=...)` in `src/agent/cli.py` — **before** the agent is created, so no spans are dropped into a no-op provider.

### 1. OpenInference → OTLP (traces, metrics, logs)

Strands emits native OTel spans. A `StrandsAgentsToOpenInferenceProcessor` transforms them into AI-aware [OpenInference](https://github.com/Arize-ai/openinference) spans (`AGENT` / `CHAIN` / `TOOL` / `LLM` span kinds, token counts, prompts) **before** a `BatchSpanProcessor` exports them via OTLP. `httpx` is auto-instrumented so the agent's trace context propagates to the wallet and vending-machine services (end-to-end distributed traces).

- **Traces** → Grafana Tempo
- **Metrics** → Grafana Mimir
- **Logs** → Grafana Loki (structured audit logs, correlated by `trace_id`)

### 2. Grafana Sigil — AI-native observability

[Grafana Sigil](https://grafana.com/) is Grafana's AI-observability SDK. It records **LLM generations and tool executions** with AI-specific semantics on top of the raw OTel traces. This project integrates it at three touch points:

| Touch point | File | What it does |
|-------------|------|--------------|
| **Client init** | `observability/telemetry.py` → `_initialize_sigil_client()` | Builds a `sigil_sdk.Client` from `ClientConfig(GenerationExportConfig(...))`. Created **after** the `TracerProvider`/`MeterProvider` are set globally, because the Sigil SDK emits its own internal OTel signals. |
| **Strands hook adapter** | `agent/agent.py` → `create_agent()` | Attaches a `SigilStrandsHookProvider`/`SigilStrandsHandler` (from `sigil_sdk_strands`) to the Strands `Agent` as a `hooks` provider, so generations are captured automatically as the agent reasons. |
| **Tool wrapper** | `observability/sigil_tools.py` → `@sigil_tool_wrapper` | Decorator that records each tool call (`tool_name`, `input_args`, `output`, `duration_ms`, `success`) via `client.start_tool_execution(...)`. Applied to high-stakes tools such as `execute_purchase`. |

**Fail-safe by design:** every Sigil call is wrapped in `try/except`. If the SDK is not installed, credentials are missing, or a recording call fails, the agent logs a warning and continues — **Sigil never changes tool behaviour or breaks a purchase.**

### Coexistence scenarios

`configure_telemetry()` degrades gracefully depending on which credentials are present:

| OTLP (Grafana) | Sigil | Behaviour |
|:--:|:--:|---|
| ✅ | ✅ | Full pipeline: OpenInference + OTLP export **and** Sigil AI observability |
| ✅ | ❌ | OpenInference + OTLP export only |
| ❌ | ✅ | TracerProvider/MeterProvider set up (no OTLP export) so Sigil can emit; Sigil active |
| ❌ | ❌ | Telemetry disabled (warning logged) |

Partial Sigil credentials (some but not all of endpoint / tenant / token) are detected and skipped with a warning rather than crashing.

### Sigil configuration

Set these in `.env` (see `.env.example`). Sigil activates only when **all three** required values are present:

```bash
# Required
SIGIL_ENDPOINT=https://sigil-prod-<region>.grafana.net/api/v1/generations:export
SIGIL_AUTH_TENANT_ID=<your-tenant-id>
SIGIL_AUTH_TOKEN=glc_<your-token>

# Optional (defaults shown)
SIGIL_PROTOCOL=http            # http | grpc | none
SIGIL_AUTH_MODE=basic          # basic → token used as basic_password; bearer/tenant → bearer_token
SIGIL_AGENT_NAME=nova
SIGIL_AGENT_VERSION=0.1.0
SIGIL_USER_ID=<user>
SIGIL_TAGS=project=get-me-a-coke,env=dev,team=dnx-ai
```

> 📚 For the full background on AI observability, OpenInference span kinds, evaluation, and HITL patterns, see [`docs/observability-deep-dive.md`](docs/observability-deep-dive.md). Its "Real-World Example: Get Me a Coke" section is reconciled against the actual source in `src/observability/` and `src/agent/`.

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
- **OTLP**: `GRAFANA_OTLP_ENDPOINT` / `GRAFANA_INSTANCE_ID` / `GRAFANA_API_TOKEN` (or the standard `OTEL_EXPORTER_OTLP_ENDPOINT` + `OTEL_EXPORTER_OTLP_HEADERS`)
- **Sigil**: `SIGIL_ENDPOINT` / `SIGIL_AUTH_TENANT_ID` / `SIGIL_AUTH_TOKEN` (see [Sigil configuration](#sigil-configuration))

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

> CDK reads the target AWS account from `CDK_DEFAULT_ACCOUNT` (or the `account` context in `infra/cdk.json`) and region from `CDK_DEFAULT_REGION` — set these to your own values before deploying.

## Tech Stack

- Python 3.12+ / uv
- FastAPI + Mangum (vending machine, wallet service)
- Strands Agents SDK on AWS Bedrock (agent)
- NVIDIA Nemotron Nano 3 30B via Bedrock (model)
- OpenTelemetry + OpenInference → Grafana Cloud (traces/metrics/logs)
- Grafana Sigil SDK (`sigil-sdk`, `sigil-sdk-strands`) — AI-native observability
- AWS Step Functions (human-in-the-loop approval gate)
- AWS CDK (infrastructure)

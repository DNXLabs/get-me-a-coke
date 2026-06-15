# Component Methods: Get Me a Coke

## Vending Machine API Methods

### app.py — Application Factory

| Method | Signature | Purpose |
|--------|-----------|---------|
| `create_app` | `() -> FastAPI` | Create and configure the FastAPI application with routes |

### routes.py — API Endpoints

| Method | Signature | Purpose |
|--------|-----------|---------|
| `list_products` | `() -> list[Product]` | Return all available products from catalog |
| `health_check` | `() -> dict` | Return service health status |
| `purchase` | `(product_id: str, request: Request) -> JSONResponse` | Handle purchase flow: return 402 or dispense product |

### x402.py — Payment Handling

| Method | Signature | Purpose |
|--------|-----------|---------|
| `get_payment_terms` | `(product: Product) -> PaymentTerms` | Generate 402 response payload with payment terms |
| `validate_payment` | `(payment_header: str) -> bool` | Validate payment header (MVP: accept any non-empty value) |

### models.py — Data Models

| Model | Fields | Purpose |
|-------|--------|---------|
| `Product` | `id, name, price_usd, currency, network, wallet_address` | Product catalog item |
| `PaymentTerms` | `price, currency, network, wallet_address` | x402 payment terms in 402 response |
| `PurchaseResponse` | `status, product_id, product_name` | Successful purchase confirmation |

### handler.py — Lambda Entry Point

| Method | Signature | Purpose |
|--------|-----------|---------|
| `handler` | `(event, context) -> dict` | Mangum wrapper for Lambda invocation |

---

## Agent Methods

### agent.py — Agent Definition

| Method | Signature | Purpose |
|--------|-----------|---------|
| `create_agent` | `() -> Agent` | Create Strands agent with tools, model, and payments plugin |
| `get_system_prompt` | `() -> str` | Return the agent's system prompt |

### cli.py — CLI Entry Point

| Method | Signature | Purpose |
|--------|-----------|---------|
| `main` | `() -> None` | Parse CLI args and dispatch to single-shot or REPL mode |
| `run_single_shot` | `(instruction: str) -> None` | Execute single instruction and exit |
| `run_interactive` | `() -> None` | Start interactive REPL loop |

### tools/ — Agent Tools

| Tool | Signature | Purpose |
|------|-----------|---------|
| `http_request` | (from `strands_tools`) | Make HTTP requests to vending machine API |

**Note**: The agent uses `http_request` from `strands_tools` as its primary tool. AgentCore Payments plugin handles 402 detection and payment automatically — no custom payment tool needed.

---

## Observability Methods

### telemetry.py — Telemetry Configuration

| Method | Signature | Purpose |
|--------|-----------|---------|
| `configure_telemetry` | `() -> None` | Initialize OTel providers with OpenInference span processor and OTLP exporters |
| `get_tracer_provider` | `() -> TracerProvider` | Create TracerProvider with StrandsAgentsToOpenInferenceProcessor + OTLP exporter to Grafana |
| `get_meter_provider` | `() -> MeterProvider` | Create MeterProvider with OTLP exporter to Grafana |
| `get_logger_provider` | `() -> LoggerProvider` | Create LoggerProvider with OTLP exporter to Grafana |

**Key Implementation Detail**: Strands SDK natively emits OpenTelemetry spans. The `openinference-instrumentation-strands-agents` package provides `StrandsAgentsToOpenInferenceProcessor` — a span processor that transforms Strands' native OTel spans into OpenInference semantic format. Processor ordering matters: the OpenInference processor must run before the OTLP exporter so that Grafana receives properly formatted spans.

```python
# Correct wiring pattern:
from openinference.instrumentation.strands_agents import StrandsAgentsToOpenInferenceProcessor

provider = TracerProvider()
# 1. Transform Strands spans → OpenInference format
provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())
# 2. Export transformed spans to Grafana
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(...)))
trace.set_tracer_provider(provider)
# Strands reads the global tracer provider automatically — no explicit instrument() call needed
```

### config.py — Configuration

| Method | Signature | Purpose |
|--------|-----------|---------|
| `load_config` | `() -> Config` | Load configuration from `.env` file |

---

## Infrastructure Methods (CDK)

### app.py — CDK App Entry Point

| Method | Signature | Purpose |
|--------|-----------|---------|
| CDK App | `cdk.App()` | Define CDK application with stacks |

### vending_machine_stack.py — Vending Machine Stack

| Construct | Purpose |
|-----------|---------|
| `VendingMachineStack` | Lambda function + API Gateway HTTP API |

### agent_stack.py — Agent Stack

| Construct | Purpose |
|-----------|---------|
| `AgentStack` | AgentCore Runtime configuration + IAM roles |

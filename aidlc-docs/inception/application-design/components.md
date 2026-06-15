# Components: Get Me a Coke

## Component 1: Vending Machine API

| Attribute | Detail |
|-----------|--------|
| **Name** | `vending_machine` |
| **Type** | REST API Service |
| **Framework** | FastAPI + Mangum |
| **Deployment** | AWS Lambda behind API Gateway (HTTP API) |
| **Responsibility** | x402-compatible seller — exposes product catalog and accepts payments |

### Responsibilities
- Serve product catalog (list available products with prices)
- Implement x402 payment flow (return 402 with payment terms when unpaid)
- Validate payment headers (mock: accept any X-PAYMENT header)
- Dispense products on valid payment
- Handle errors (unknown products, invalid requests)
- Provide health check endpoint

### Interfaces
- `GET /products` — List all available products
- `GET /health` — Health check
- `POST /purchase/{product_id}` — Purchase a product (returns 402 or 200)

---

## Component 2: AI Agent

| Attribute | Detail |
|-----------|--------|
| **Name** | `agent` |
| **Type** | Autonomous AI Agent |
| **Framework** | Strands Agents SDK |
| **Model** | nvidia.nemotron-nano-3-30b (via Bedrock) |
| **Deployment** | AgentCore Runtime (managed, serverless) |
| **Responsibility** | Autonomous buyer — discovers, reasons, pays, and confirms purchases |

### Responsibilities
- Accept user instructions (single-shot or interactive REPL)
- Discover available products from vending machine catalog
- Reason about which product to purchase based on user request
- Execute x402 payment flow via AgentCore Payments plugin
- Report purchase results to user (minimal output)
- Handle errors gracefully with clear messages
- Support general conversation in REPL mode

### Interfaces
- CLI single-shot: `python -m agent.cli "<instruction>"`
- CLI interactive: `python -m agent.cli --interactive`
- AgentCore Runtime endpoint (when deployed)

---

## Component 3: Observability

| Attribute | Detail |
|-----------|--------|
| **Name** | `observability` |
| **Type** | Cross-cutting concern (instrumentation layer) |
| **Framework** | OpenTelemetry SDK + OpenInference |
| **Deployment** | Embedded in agent process |
| **Responsibility** | Capture and export traces, metrics, and logs to Grafana Cloud |

### Responsibilities
- Transform Strands' native OTel spans into OpenInference semantic format via `StrandsAgentsToOpenInferenceProcessor`
- Export traces to Grafana Tempo via OTLP
- Export metrics (token usage, latency, payment amounts) to Grafana Mimir
- Export structured logs to Grafana Loki
- Configure exporters from `.env` credentials
- Ensure correct processor ordering (OpenInference processor before OTLP exporter)

### Interfaces
- `configure_telemetry()` — Initialize OTel providers with OpenInference processor and exporters
- Strands reads the global tracer provider automatically — no explicit `instrument()` call needed

### Key Technical Detail
The package `openinference-instrumentation-strands-agents` provides `StrandsAgentsToOpenInferenceProcessor`, which is a **span processor** (not a traditional instrumentor). Strands SDK natively emits OTel spans; this processor transforms them into OpenInference semantic conventions (agent spans, tool call spans, LLM spans with token counts, etc.).

---

## Component 4: Infrastructure

| Attribute | Detail |
|-----------|--------|
| **Name** | `infra` |
| **Type** | Infrastructure as Code |
| **Framework** | AWS CDK (Python) |
| **Deployment** | CloudFormation stacks |
| **Responsibility** | Define and deploy all AWS resources |

### Responsibilities
- Define Lambda function for vending machine API
- Define API Gateway (HTTP API) routing to Lambda
- Define AgentCore Runtime configuration for agent
- Define IAM roles and policies
- Manage environment configuration

### Interfaces
- `cdk deploy` — Deploy all stacks
- `cdk destroy` — Tear down all resources
- `cdk synth` — Synthesize CloudFormation templates

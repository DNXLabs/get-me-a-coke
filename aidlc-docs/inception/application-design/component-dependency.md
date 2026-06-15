# Component Dependencies: Get Me a Coke

## Dependency Matrix

| Component | Depends On | Communication | Coupling |
|-----------|-----------|---------------|----------|
| Vending Machine API | None (standalone) | — | Independent |
| Agent | Vending Machine API, Bedrock, AgentCore Payments, Observability | HTTP, SDK | Loose (via HTTP + plugins) |
| Observability | Grafana Cloud | OTLP/HTTP | Loose (export-only) |
| Infrastructure (CDK) | All components (defines their deployment) | CloudFormation | Deployment-time only |

## Dependency Graph

```
+-------------------+
|   AI Engineer     |
|   (CLI user)      |
+--------+----------+
         |
         | stdin/stdout
         v
+--------+----------+       HTTP (REST)       +---------------------+
|      Agent        | ----------------------> | Vending Machine API |
|  (Strands SDK)    |                         |     (FastAPI)       |
+--------+----------+                         +---------------------+
         |
         | SDK calls
         v
+--------+----------+
| AgentCore Payments|
|   (402 handler)   |
+-------------------+
         |
         | AWS SDK
         v
+--------+----------+
|   Bedrock         |
| (Nemotron Nano)   |
+-------------------+

         Agent also exports to:
         |
         | OTLP/HTTP
         v
+--------+----------+
|  Grafana Cloud    |
| (Tempo/Mimir/Loki)|
+-------------------+
```

## Communication Patterns

### Agent → Vending Machine API
- **Protocol**: HTTP/HTTPS (REST)
- **Pattern**: Synchronous request-response
- **Data Format**: JSON
- **Authentication**: None (PoC) — API Gateway provides TLS
- **Error Handling**: Agent interprets HTTP status codes (200, 402, 404)

### Agent → Bedrock
- **Protocol**: AWS SDK (HTTP under the hood)
- **Pattern**: Synchronous inference call
- **Data Format**: Bedrock API format (managed by Strands SDK)
- **Authentication**: IAM role (via AWS profile or AgentCore Runtime role)

### Agent → AgentCore Payments
- **Protocol**: SDK (internal to agent process)
- **Pattern**: Interceptor — automatically handles 402 responses
- **Data Format**: Internal SDK types
- **Authentication**: AgentCore Identity (Coinbase CDP credentials)

### Agent → Grafana Cloud
- **Protocol**: OTLP over HTTP
- **Pattern**: Async batch export (fire-and-forget)
- **Data Format**: OpenTelemetry Protocol Buffers
- **Authentication**: Basic auth (instance ID + API token from .env)

## Build-Time Dependencies

| Component | Key Python Dependencies |
|-----------|------------------------|
| Vending Machine API | `fastapi`, `mangum`, `uvicorn` (dev), `pydantic` |
| Agent | `strands-agents`, `strands-agents-tools`, `bedrock-agentcore[strands-agents]`, `httpx` |
| Observability | `opentelemetry-sdk`, `opentelemetry-exporter-otlp`, `openinference-instrumentation-strands-agents` |
| Infrastructure | `aws-cdk-lib`, `constructs` |

## Deployment Dependencies

| Component | Deploys To | Depends On (Runtime) |
|-----------|-----------|---------------------|
| Vending Machine API | Lambda + API Gateway | None |
| Agent | AgentCore Runtime | Vending Machine API URL, Bedrock access, Payment Manager |
| Infrastructure | CloudFormation | AWS account, CDK bootstrap |

## Deployment Order
1. **Vending Machine API** (independent — can deploy first)
2. **Agent** (needs vending machine URL as configuration)
3. Both can be deployed via single `cdk deploy` command

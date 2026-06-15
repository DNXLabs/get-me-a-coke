# Units of Work: Get Me a Coke

## Decomposition Summary

| Unit | Name | Type | Deployment | Development Order |
|------|------|------|------------|-------------------|
| 1 | Vending Machine API | Service | Lambda + API Gateway | Can start immediately |
| 2 | AI Agent | Service | AgentCore Runtime | After Unit 1 (needs API URL for integration test) |
| 3 | Observability | Module | Embedded in Agent | After Unit 2 (instruments agent) |
| 4 | Infrastructure | IaC | CloudFormation (CDK) | In parallel with Units 1-3 |

---

## Unit 1: Vending Machine API

| Attribute | Detail |
|-----------|--------|
| **Scope** | FastAPI application implementing x402 seller pattern |
| **Package** | `src/vending_machine/` |
| **Deployment** | AWS Lambda (via Mangum) + API Gateway HTTP API |
| **Dependencies** | None (fully independent) |
| **Stories** | 1.1, 1.2, 1.3, 1.4 |

### Responsibilities
- Product catalog endpoint (GET /products)
- Purchase endpoint with x402 flow (POST /purchase/{product_id})
- Health check endpoint (GET /health)
- Payment validation (mock: accept any X-PAYMENT header)
- Error handling (404 for unknown products)

### Key Files
```
src/vending_machine/
├── __init__.py
├── app.py          # FastAPI app factory + route registration
├── routes.py       # API endpoint handlers
├── models.py       # Pydantic models (Product, PaymentTerms, PurchaseResponse)
├── x402.py         # x402 payment handling logic
└── handler.py      # Lambda entry point (Mangum wrapper)
```

### Testing
- Unit tests with FastAPI TestClient
- No external dependencies to mock

---

## Unit 2: AI Agent

| Attribute | Detail |
|-----------|--------|
| **Scope** | Strands SDK agent with AgentCore Payments plugin |
| **Package** | `src/agent/` |
| **Deployment** | AgentCore Runtime |
| **Dependencies** | Unit 1 (vending machine URL for integration tests) |
| **Stories** | 2.1, 2.2, 2.3, 2.4, 2.5, 2.6 |

### Responsibilities
- Agent definition with system prompt and tools
- CLI entry point (single-shot + interactive REPL)
- AgentCore Payments plugin configuration
- Graceful error handling and user-facing messages
- General conversation capability in REPL mode

### Key Files
```
src/agent/
├── __init__.py
├── agent.py        # Agent definition, system prompt, tools, payments plugin
├── cli.py          # CLI entry point (argparse, single-shot + REPL)
├── config.py       # Configuration loading from .env
└── tools/          # Custom tools (if needed beyond http_request)
    └── __init__.py
```

### Testing
- Unit tests with mocked Bedrock responses and mocked HTTP calls
- Integration tests with real Bedrock (Nemotron Nano) but mocked payments

---

## Unit 3: Observability

| Attribute | Detail |
|-----------|--------|
| **Scope** | OpenTelemetry + OpenInference telemetry wiring |
| **Package** | `src/observability/` |
| **Deployment** | Embedded in agent process (imported by agent at startup) |
| **Dependencies** | Unit 2 (instruments the agent) |
| **Stories** | 3.1, 3.2, 3.3 |

### Responsibilities
- Configure TracerProvider with StrandsAgentsToOpenInferenceProcessor
- Configure OTLP exporters for traces, metrics, logs → Grafana Cloud
- Load Grafana credentials from .env
- Ensure correct processor ordering (OpenInference before OTLP export)

### Key Files
```
src/observability/
├── __init__.py
├── telemetry.py    # configure_telemetry(), provider setup, processor wiring
└── exporters.py    # OTLP exporter configuration (traces, metrics, logs)
```

### Testing
- Unit tests verifying processor ordering and configuration
- Integration test verifying spans are emitted (mock OTLP endpoint)

---

## Unit 4: Infrastructure (CDK)

| Attribute | Detail |
|-----------|--------|
| **Scope** | AWS CDK stacks for all project resources |
| **Package** | `infra/` |
| **Deployment** | CloudFormation stacks via `cdk deploy` |
| **Dependencies** | Units 1, 2, 3 (defines their deployment targets) |
| **Stories** | 4.1, 4.2, 4.3 |

### Responsibilities
- Vending Machine stack: Lambda function + API Gateway HTTP API
- Agent stack: AgentCore Runtime configuration + project-specific IAM role
- IAM role with Nemotron Nano invoke permissions (new role, follows foundation pattern)
- Environment configuration (SSM parameters or stack outputs)

### Key Files
```
infra/
├── app.py                      # CDK app entry point
├── stacks/
│   ├── __init__.py
│   ├── vending_machine_stack.py  # Lambda + API Gateway
│   └── agent_stack.py            # AgentCore Runtime + IAM
├── cdk.json
└── requirements.txt            # CDK dependencies (separate from app)
```

### Design Decisions
- **New stacks** — do NOT modify existing DNXFoundation stacks
- **Follow foundation pattern** — same naming conventions, same CDK patterns
- **Project-specific IAM role** — allows `nvidia.nemotron-nano-3-30b` invocation (existing foundation role only allows Claude Sonnet 4)
- **Stack naming**: `GetMeACoke-VendingMachine-dev`, `GetMeACoke-Agent-dev`

### Testing
- `cdk synth` validates templates
- No runtime tests for infrastructure

---

## Code Organization (Monorepo)

```
get-me-a-coke/
├── src/
│   ├── vending_machine/    # Unit 1
│   ├── agent/              # Unit 2
│   └── observability/      # Unit 3
├── tests/
│   ├── unit/
│   │   ├── test_vending_machine/
│   │   ├── test_agent/
│   │   └── test_observability/
│   └── integration/
│       ├── test_agent_integration.py
│       └── conftest.py
├── infra/                  # Unit 4
│   ├── app.py
│   ├── stacks/
│   ├── cdk.json
│   └── requirements.txt
├── pyproject.toml          # App dependencies (units 1-3)
├── .env                    # Local config
├── .env.example
└── ...
```

### pyproject.toml Dependency Groups
- **default**: Core app dependencies (fastapi, strands-agents, etc.)
- **dev**: Development tools (pytest, mypy, ruff, uvicorn)
- **test**: Test-specific (moto, pytest-cov, httpx for TestClient)

Infrastructure (`infra/`) uses its own `requirements.txt` with `aws-cdk-lib` and `constructs` — kept separate to avoid polluting the app's dependency tree.

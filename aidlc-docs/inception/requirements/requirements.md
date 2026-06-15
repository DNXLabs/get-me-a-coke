# Requirements: Get Me a Coke

## Intent Analysis

| Attribute | Value |
|-----------|-------|
| **User Request** | Build a PoC demonstrating autonomous agent-to-service commerce using x402 payment protocol |
| **Request Type** | New Project (Greenfield) |
| **Scope Estimate** | Multiple Components (Vending Machine API + Agent + Observability + Infrastructure) |
| **Complexity Estimate** | Moderate (multiple integrations, but well-defined patterns) |
| **Requirements Depth** | Standard |

---

## Functional Requirements

### FR-1: Vending Machine API (x402 Seller)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Expose a product catalog endpoint (`GET /products`) returning available products with name, price, currency, and network | Must |
| FR-1.2 | Support 2-3 hardcoded products (e.g., coke, water, juice) with different prices | Must |
| FR-1.3 | Return HTTP 402 with payment terms (price, currency, network, wallet address) when purchase endpoint is called without payment | Must |
| FR-1.4 | Accept any request with an `X-PAYMENT` header (any value) as valid payment for MVP | Must |
| FR-1.5 | Return product dispensed confirmation (HTTP 200 with product details) on valid payment | Must |
| FR-1.6 | Return HTTP 404 for unknown product IDs | Must |
| FR-1.7 | Expose health check endpoint (`GET /health`) | Should |

### FR-2: AI Agent (x402 Buyer via AgentCore)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Use Strands Agents SDK with NVIDIA Nemotron Nano 3 30B model (`nvidia.nemotron-nano-3-30b`) via Bedrock | Must |
| FR-2.2 | Integrate AgentCore Payments plugin for automatic x402 payment handling | Must |
| FR-2.3 | Agent can discover available products from vending machine catalog endpoint | Must |
| FR-2.4 | Agent can autonomously execute purchase flow (discover → select → pay → confirm) | Must |
| FR-2.5 | Agent confirms receipt of purchased item and reports result to user | Must |
| FR-2.6 | CLI supports single-shot mode: `python -m agent.cli "Buy me a coke"` | Must |
| FR-2.7 | CLI supports interactive REPL mode: `python -m agent.cli --interactive` | Must |
| FR-2.8 | Agent uses `http_request` tool from `strands_tools` for HTTP calls | Must |

### FR-3: Observability

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Instrument Strands agent with OpenInference tracing via `StrandsAgentsToOpenInferenceProcessor` span processor | Must |
| FR-3.2 | Export all traces to Grafana Cloud via OTLP (configured in `.env`) | Must |
| FR-3.3 | Capture agent reasoning loops, tool calls, and payment transactions as spans | Must |
| FR-3.4 | Export metrics (token usage, latency, payment amounts) via OTLP to Grafana Mimir | Should |
| FR-3.5 | Export structured logs via OTLP to Grafana Loki | Should |

### FR-4: Infrastructure

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Define all infrastructure as CDK (Python) | Must |
| FR-4.2 | Deploy vending machine API as Lambda + API Gateway (HTTP API) | Must |
| FR-4.3 | Deploy agent to AgentCore Runtime | Must |
| FR-4.4 | All resources in `ap-southeast-2` (Sydney) | Must |
| FR-4.5 | Use AWS profile `nonprod-dnxai` for deployment | Must |

---

## Non-Functional Requirements

### NFR-1: Development Experience

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-1.1 | Python 3.12+ with `uv` for all package management | Must |
| NFR-1.2 | Local development: `uvicorn` for API, CLI script for agent | Must |
| NFR-1.3 | All configuration via `.env` file (Grafana credentials, AWS profile, region) | Must |
| NFR-1.4 | AgentCore Payments prerequisites documented as manual setup steps | Must |

### NFR-2: Code Quality

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-2.1 | `ruff` for linting and formatting | Must |
| NFR-2.2 | `mypy` strict mode for type checking | Must |
| NFR-2.3 | `pytest` with `pytest-cov` for testing | Must |

### NFR-3: Testing Strategy

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-3.1 | Unit tests with mocked external calls (Bedrock, AgentCore, HTTP) | Must |
| NFR-3.2 | Integration tests with real Bedrock model calls but mocked payments | Must |
| NFR-3.3 | `moto` for mocking AWS services in unit tests | Should |
| NFR-3.4 | Property-based testing for pure functions and serialization round-trips only | Should |

### NFR-4: Security (PoC Level)

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-4.1 | Security extension rules NOT enforced (PoC project) | N/A |
| NFR-4.2 | Agent wallet uses testnet USDC only | Must |
| NFR-4.3 | TLS via API Gateway (default, no custom config) | Must |

### NFR-5: Performance

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-5.1 | No specific performance targets (PoC) | N/A |
| NFR-5.2 | Lambda cold start acceptable for demo purposes | N/A |

---

## Technical Constraints

| Constraint | Detail |
|------------|--------|
| **Prohibited** | LangChain, LangGraph, Flask, Django, pip, poetry, pipenv, black, flake8, isort, requests |
| **Required** | Strands Agents SDK, FastAPI, uv, ruff, httpx, AgentCore Payments plugin |
| **Model** | nvidia.nemotron-nano-3-30b (via Bedrock) |
| **Region** | ap-southeast-2 (Sydney) |
| **Network** | Base Sepolia testnet for payments |
| **Observability** | Grafana Cloud (Tempo + Mimir + Loki) via OTLP |

---

## Extension Configuration

| Extension | Enabled | Decided At |
|-----------|---------|------------|
| Security Baseline | No | Requirements Analysis |
| Property-Based Testing | Partial (pure functions + serialization only) | Requirements Analysis |

---

## Out of Scope (MVP)

- Web/visual interface
- Slack integration
- Real on-chain payment validation (seller side)
- Multiple agent coordination
- Persistent agent memory
- Production security hardening
- Console trace exporter (Grafana Cloud only)

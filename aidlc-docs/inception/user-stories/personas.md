# Personas: Get Me a Coke

## Persona 1: AI Engineer (Thiago)

| Attribute | Detail |
|-----------|--------|
| **Role** | AI Engineer at DNX |
| **Goal** | Test agent payment flows end-to-end, validate Strands Agents patterns, implement AI observability |
| **Context** | Solo developer building a PoC to establish agent-to-service commerce patterns |
| **Technical Level** | Expert — comfortable with AWS, Python, AI/ML tooling |
| **Interaction** | CLI-based (single-shot commands and interactive REPL) |
| **Success Criteria** | Agent completes autonomous purchase without human intervention; full observability traces captured |

### Needs
- Quick local development cycle (run API + agent locally)
- Clear, minimal CLI output showing purchase results
- Full observability traces in Grafana for debugging and learning
- Deployable to AWS Lambda / AgentCore Runtime

### Frustrations
- Complex setup procedures that block getting started
- Opaque agent behavior (can't see what happened)
- Flaky integrations that fail silently

---

## Persona 2: AI Agent (Autonomous Actor)

| Attribute | Detail |
|-----------|--------|
| **Role** | Autonomous software agent |
| **Goal** | Discover, pay for, and consume services without human intervention |
| **Context** | Runs on AgentCore Runtime, uses Strands SDK with Nemotron Nano model |
| **Capabilities** | HTTP requests, x402 payment via AgentCore Payments plugin, natural language reasoning |
| **Interaction** | Receives instructions from AI Engineer via CLI; interacts with Vending Machine API autonomously |

### Behaviors
- Reasons about available products and selects appropriate one
- Handles x402 payment flow automatically via AgentCore plugin
- Reports results back to the user (minimal output)
- Handles failures gracefully with clear error messages
- In REPL mode, can hold general conversation and execute purchases when asked

---

## Persona 3: Vending Machine API (Service)

| Attribute | Detail |
|-----------|--------|
| **Role** | x402-compatible service (seller) |
| **Goal** | Accept agent payments and dispense products |
| **Context** | FastAPI application running on Lambda behind API Gateway |
| **Interaction** | Receives HTTP requests from agents; returns 402 payment terms or dispenses products |

### Behaviors
- Exposes product catalog for discovery
- Returns HTTP 402 with payment terms when no payment provided
- Accepts any X-PAYMENT header as valid payment (MVP mock)
- Dispenses product on valid payment
- Returns appropriate errors for unknown products

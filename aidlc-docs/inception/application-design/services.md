# Services: Get Me a Coke

## Service Architecture Overview

This system uses a simple client-server pattern with an autonomous agent as the client:

```
AI Engineer → Agent (CLI) → Vending Machine API
                 ↓                    ↓
         AgentCore Payments     x402 Payment Terms
                 ↓
         Grafana (Observability)
```

---

## Service 1: Vending Machine Service

| Attribute | Detail |
|-----------|--------|
| **Type** | Stateless REST API |
| **Orchestration** | None — responds to individual requests |
| **State** | Stateless (product catalog is hardcoded) |

### Service Behavior
1. Receives HTTP request from agent
2. Routes to appropriate handler (catalog, purchase, health)
3. For purchases: checks for payment header → returns 402 or dispenses
4. Returns JSON response

### No Orchestration Needed
The vending machine is a simple request-response service. No saga, no workflow, no state machine. Each request is independent.

---

## Service 2: Agent Service

| Attribute | Detail |
|-----------|--------|
| **Type** | Autonomous reasoning agent |
| **Orchestration** | Strands SDK agent loop (plan → act → observe) |
| **State** | Conversation state within a session (not persisted) |

### Service Behavior — Purchase Flow
1. Receive user instruction (e.g., "Buy me a coke")
2. **Plan**: Determine steps needed (discover products → select → purchase)
3. **Act**: Call `http_request` tool to query catalog
4. **Observe**: Parse catalog response, select product
5. **Act**: Call `http_request` tool to purchase
6. **Observe**: Receive 402 → AgentCore Payments plugin auto-handles payment → retry succeeds
7. **Report**: Return minimal result to user

### Orchestration Pattern
The Strands SDK provides the orchestration loop. The agent doesn't need custom orchestration code — the model drives the plan-act-observe cycle. AgentCore Payments plugin intercepts 402 responses transparently.

---

## Service 3: Observability Service

| Attribute | Detail |
|-----------|--------|
| **Type** | Instrumentation layer (not a standalone service) |
| **Orchestration** | None — passive data collection |
| **State** | Stateless (exports data, doesn't store it) |

### Service Behavior
1. `configure_telemetry()` called at agent startup
2. Sets up TracerProvider with `StrandsAgentsToOpenInferenceProcessor` (transforms Strands native spans → OpenInference format)
3. Adds OTLP exporter after the OpenInference processor (order matters)
4. Sets the TracerProvider as global — Strands reads it automatically
5. OTel SDK batches and exports spans/metrics/logs to Grafana via OTLP
6. No explicit `instrument()` call needed — Strands emits OTel spans natively, processor transforms them

---

## Service Interactions

| From | To | Protocol | Purpose |
|------|-----|----------|---------|
| AI Engineer | Agent CLI | stdin/stdout | Issue instructions, receive results |
| Agent | Vending Machine API | HTTP (REST) | Discover products, attempt purchases |
| Agent | Bedrock | AWS SDK (HTTP) | Model inference (reasoning) |
| Agent | AgentCore Payments | SDK (internal) | Automatic 402 payment handling |
| Agent | Grafana Cloud | OTLP (HTTP) | Export traces, metrics, logs |

---

## No Service Mesh / Message Queue Needed

This is a simple PoC with synchronous request-response patterns:
- Agent calls API directly via HTTP
- No async messaging, no event bus, no service mesh
- No service discovery needed (agent knows the vending machine URL)
- No circuit breaker or retry logic beyond what AgentCore provides

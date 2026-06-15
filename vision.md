# Vision: Get Me a Coke

## Executive Summary

Get Me a Coke is a proof-of-concept demonstrating **Bedrock AgentCore Runtime**, **decoupled agent-to-service commerce**, and **AI observability** on AWS. It showcases an AI agent (Strands SDK on AgentCore) that discovers products from a vending machine API, requests human approval, pays via a shared wallet service, and is fully observable through OpenTelemetry + Sigil.

## Problem Statement

AI agents need to autonomously interact with services — discover, negotiate, and transact — while maintaining human oversight, auditability, and full observability. There is no established pattern at DNX for:
1. Deploying agents on Bedrock AgentCore Runtime
2. Decoupled payment services with authentication/authorization
3. Human-in-the-loop approval gates for agent actions
4. End-to-end AI observability (reasoning → tool calls → transactions)

This project creates a minimal reference implementation covering all four.

## Target Users

| User Type | Need |
|-----------|------|
| AI Engineer | Validate AgentCore Runtime patterns, Strands SDK, decoupled service architecture |
| Platform Team | Reference for agent deployment, observability, and audit patterns on AWS |

## Success Metrics

| Metric | Target |
|--------|--------|
| Agent runs on AgentCore Runtime | Deployed and accessible via `bedrock-agentcore chat` CLI |
| Human-in-the-loop enforced | Agent cannot purchase without user approval (audited gate) |
| Decoupled wallet service | Shared payment service with API key auth, independently deployable |
| Observability traces captured | Full trace from agent reasoning → tool call → payment → response |
| Audit trail | Every purchase approval logged with user_id, timestamp, context |
| System prompt decoupled | Loaded from SSM Parameter Store, updatable without redeploy |

## Architecture

```
User ←→ bedrock-agentcore chat CLI ←→ AgentCore Runtime (container)
                                              │
                                              ├── tool: list_products → Vending Machine API (Lambda)
                                              ├── tool: get_purchase_quote → Vending Machine API
                                              ├── tool: execute_purchase → Wallet Service (Lambda)
                                              │                              └── API key auth
                                              └── tool: wallet_get_balance → Wallet Service
                                              
Observability: OpenTelemetry + Sigil → Grafana Cloud
Audit: Structured JSON logs → CloudWatch Logs
Prompt: SSM Parameter Store (versioned, update without redeploy)
```

## Full Scope Vision

### Vending Machine API (Lambda + API Gateway)
- x402 payment flow (HTTP 402 + payment terms)
- Product catalog endpoint
- Stateless, publicly accessible

### Wallet Service (Lambda + API Gateway)
- Shared payment service — any authorized agent can use it
- API key authentication (X-API-Key header)
- Balance check + payment execution
- Mock USDC wallet for POC (replaceable with real Coinbase CDP / AgentCore Payments)

### Agent (AgentCore Runtime)
- Strands SDK + Bedrock model (Nemotron Nano 3 30B)
- Two-step purchase flow with mandatory human approval
- System prompt loaded from SSM Parameter Store
- Audit logging on every purchase decision
- Accessible via `bedrock-agentcore chat` CLI

### Observability
- OpenTelemetry tracing (agent reasoning, tool calls, HTTP requests)
- Sigil SDK for AI-specific generation tracking
- Structured audit logs for purchase approvals (CloudWatch)

### Human-in-the-Loop
- Conversational approval: agent shows quote, waits for user confirmation
- Tool-level enforcement: `execute_purchase` refuses without prior quote
- Audit trail: user_id, timestamp, product, price logged on every approval

## MVP Scope — Features IN

| Feature | Rationale |
|---------|-----------|
| Vending Machine API (Lambda) with x402 flow | Core selling side |
| Wallet Service (Lambda) with API key auth | Decoupled, shared payment service |
| Agent on AgentCore Runtime (Strands SDK) | Core AgentCore pattern |
| Two-step purchase with HITL approval gate | Human oversight, auditable |
| System prompt in SSM Parameter Store | Decoupled from code, best practice |
| AI observability (OpenTelemetry + Sigil) | Key learning objective |
| Structured audit logging | Compliance/governance pattern |
| CLI interaction via `bedrock-agentcore chat` | Simple UX for POC |

## MVP Scope — Features OUT

| Feature | Reason | Target Phase |
|---------|--------|--------------|
| Web UI / Slack integration | CLI sufficient for POC | Phase 2 |
| Real on-chain payments (seller validation) | Mock sufficient; proves the pattern | Phase 2 |
| Multiple agents sharing wallet | Single agent proves auth pattern | Phase 2 |
| Persistent agent memory | Not needed for single-transaction flow | Phase 2 |
| Production security hardening | POC scope | Phase 2 |
| Bedrock Prompt Management (A/B testing) | SSM sufficient for POC | Phase 2 |

## Risks and Open Questions

| Risk/Question | Impact | Notes |
|---------------|--------|-------|
| AgentCore Runtime HITL mechanism | Medium — conversational approval works but LLM could theoretically skip | Tool-level gate (`execute_purchase` requires quote) mitigates |
| SSM Parameter Store 8KB limit | Low — system prompts rarely exceed this | Can split if needed |
| Nemotron Nano 3 30B tool-calling quality | Medium — may need to swap model if tool use is unreliable | Fallback: Claude Haiku 4.5 |
| AgentCore container build/push | Setup overhead | Need ECR repo + Dockerfile |

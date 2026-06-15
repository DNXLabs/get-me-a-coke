# Requirements Verification Questions

Please answer the following questions to help clarify the requirements for the "Get Me a Coke" project. Fill in the letter choice after each [Answer]: tag.

---

## Question 1
What is the MVP product catalog scope? The vision mentions "multiple products/prices" in full scope but the MVP examples only show "coke".

A) Single product only ("coke") for MVP — simplest possible catalog
B) 2-3 hardcoded products (e.g., coke, water, juice) — demonstrates catalog without complexity
C) Dynamic product catalog loaded from configuration (e.g., JSON file or environment variable)
D) Other (please describe after [Answer]: tag below)

[Answer]: 2

---

## Question 2
How should the vending machine validate payments in MVP? The vision says "mock validation" but what level of mock?

A) Accept any request that has an X-PAYMENT header (any value) — simplest possible
B) Accept any well-formed payment header (validate structure/format but not cryptographic proof)
C) Validate against a hardcoded test payment token — slightly more realistic
D) Other (please describe after [Answer]: tag below)

[Answer]: 1

---

## Question 3
What Bedrock model should the agent use for reasoning? (I noticed bedrock-model-selection.md exists in the workspace)

A) Claude Sonnet 4 (us.anthropic.claude-sonnet-4-20250514-v1:0) — strong reasoning, good cost balance
B) Claude 3.5 Haiku (anthropic.claude-3-5-haiku-20241022-v1:0) — fast and cheap, good for simple tool-use
C) Claude 3.5 Sonnet v2 (anthropic.claude-3-5-sonnet-20241022-v2:0) — proven, widely available
D) Let me specify from bedrock-model-selection.md
E) Other (please describe after [Answer]: tag below)

[Answer]: nvidia.nemotron-nano-3-30b

---

## Question 4
What is the agent's CLI interaction model for MVP?

A) Single-shot: run a command like `python -m agent.cli "Buy me a coke"` and it executes then exits
B) Interactive REPL: start the agent and have a conversation loop
C) Both — single-shot by default, with a `--interactive` flag for REPL mode
D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 5
For observability, should the MVP include a local development mode (e.g., console exporter for traces) or always require Grafana Cloud credentials?

A) Always require Grafana Cloud — keep it simple, one path
B) Local console exporter as default, Grafana Cloud when credentials are configured
C) Both exporters always active (console + Grafana when configured)
D) Other (please describe after [Answer]: tag below)

[Answer]:  A, config in .env

---

## Question 6
How should the project handle the AgentCore Payments prerequisites (wallet provisioning, payment manager creation) for local development?

A) Document the manual setup steps — developer runs them once before first use
B) Provide a setup script that automates the AgentCore provisioning via CLI/SDK
C) Mock the entire payment flow locally (no real AgentCore calls during dev) and only use real AgentCore when deployed
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 7
What testing strategy for the agent component? The agent calls external services (Bedrock, AgentCore, vending machine).

A) Unit tests only with mocked external calls (Bedrock responses, payment flow)
B) Unit tests with mocks + integration test against local vending machine (agent calls real local API, but Bedrock/payments mocked)
C) Unit tests with mocks + integration test with real Bedrock but mocked payments
D) Other (please describe after [Answer]: tag below)

[Answer]:  C

---

## Question 8
Should the CDK infrastructure be part of the MVP, or is manual/CLI deployment acceptable for the first iteration?

A) CDK from the start — define all infrastructure as code (Lambda, API Gateway, AgentCore)
B) AgentCore CLI for agent deployment + CDK for vending machine Lambda/API Gateway only
C) Manual/CLI deployment for MVP — add CDK in Phase 2
D) Other (please describe after [Answer]: tag below)

[Answer]: A 

---

## Question 9: Security Extensions
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)
B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 10: Property-Based Testing Extension
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, serialization, or stateful components)
B) Partial — enforce PBT rules only for pure functions and serialization round-trips (suitable for projects with limited algorithmic complexity)
C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers with no significant business logic)
D) Other (please describe after [Answer]: tag below)

[Answer]:  B

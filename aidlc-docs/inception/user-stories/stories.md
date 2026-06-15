# User Stories: Get Me a Coke

## Epic 1: Vending Machine API

### Story 1.1: Product Catalog Discovery

**As** an AI Agent, **I want** to query the vending machine's product catalog, **so that** I can discover what products are available and their prices.

**Acceptance Criteria:**
- **Given** the vending machine API is running, **When** a GET request is made to `/products`, **Then** it returns HTTP 200 with a JSON list of available products
- **Given** the catalog has products, **When** the response is received, **Then** each product includes: id, name, price (USD string), currency, and network
- **Given** the catalog is configured with 2-3 products, **When** queried, **Then** all configured products are returned

---

### Story 1.2: x402 Payment Terms Response

**As** an AI Agent, **I want** to receive clear payment terms when I attempt to purchase without paying, **so that** I know how much to pay and where to send payment.

**Acceptance Criteria:**
- **Given** a product exists, **When** a POST request is made to `/purchase/{product_id}` without an `X-PAYMENT` header, **Then** the API returns HTTP 402
- **Given** an HTTP 402 response, **When** the response is parsed, **Then** it contains: price, currency ("USDC"), network ("base-sepolia"), and wallet address
- **Given** an HTTP 402 response, **When** the headers are inspected, **Then** `X-PAYMENT-REQUIRED: true` header is present

---

### Story 1.3: Payment Acceptance and Dispensing

**As** an AI Agent, **I want** to receive my purchased product after providing payment proof, **so that** the transaction is complete.

**Acceptance Criteria:**
- **Given** a valid product ID, **When** a POST request is made to `/purchase/{product_id}` with any `X-PAYMENT` header value, **Then** the API returns HTTP 200
- **Given** a successful purchase, **When** the response is parsed, **Then** it contains: status ("dispensed") and product ID
- **Given** a successful purchase, **When** the transaction completes, **Then** the response is returned immediately (no blocking)

---

### Story 1.4: Error Handling

**As** an AI Agent, **I want** to receive clear error responses for invalid requests, **so that** I can understand what went wrong and report it to the user.

**Acceptance Criteria:**
- **Given** an unknown product ID, **When** a purchase request is made, **Then** the API returns HTTP 404 with an error message
- **Given** an invalid request format, **When** the request is processed, **Then** the API returns an appropriate HTTP error code with a descriptive message

---

## Epic 2: AI Agent

### Story 2.1: Single-Shot Purchase

**As** an AI Engineer, **I want** to run a single command to purchase a product, **so that** I can quickly test the end-to-end flow.

**Acceptance Criteria:**
- **Given** the CLI is available, **When** I run `python -m agent.cli "Buy me a coke"`, **Then** the agent executes the full purchase flow and exits
- **Given** a successful purchase, **When** the command completes, **Then** minimal output is shown (e.g., "Purchased: Coke ✓")
- **Given** a failed purchase, **When** the command completes, **Then** a clear error message is displayed explaining what went wrong

---

### Story 2.2: Interactive REPL Mode

**As** an AI Engineer, **I want** to interact with the agent in a conversational loop, **so that** I can explore its capabilities and test various scenarios.

**Acceptance Criteria:**
- **Given** the CLI is available, **When** I run `python -m agent.cli --interactive`, **Then** a REPL session starts with a prompt
- **Given** an active REPL session, **When** I type a purchase request, **Then** the agent executes the purchase and shows the result
- **Given** an active REPL session, **When** I type a general question or conversation, **Then** the agent responds naturally (general conversation capability)
- **Given** an active REPL session, **When** I type "exit" or press Ctrl+C, **Then** the session ends gracefully

---

### Story 2.3: Autonomous Product Discovery

**As** an AI Agent, **I want** to discover available products from the vending machine, **so that** I can reason about what to purchase.

**Acceptance Criteria:**
- **Given** a purchase instruction, **When** the agent begins execution, **Then** it first queries the product catalog endpoint
- **Given** a catalog response, **When** the agent processes it, **Then** it identifies available products and their prices
- **Given** multiple products available, **When** the agent reasons about the request, **Then** it selects the most appropriate product based on the user's instruction

---

### Story 2.4: Autonomous Payment Execution

**As** an AI Agent, **I want** to automatically handle the x402 payment flow, **so that** purchases complete without human intervention.

**Acceptance Criteria:**
- **Given** an HTTP 402 response from the vending machine, **When** the AgentCore Payments plugin detects it, **Then** payment is executed automatically
- **Given** payment execution, **When** the payment completes, **Then** the original request is retried with the payment proof header
- **Given** the AgentCore Payments plugin is configured, **When** a 402 is encountered, **Then** no human intervention is required

---

### Story 2.5: Purchase Confirmation

**As** an AI Engineer, **I want** the agent to confirm what it purchased, **so that** I know the transaction succeeded.

**Acceptance Criteria:**
- **Given** a successful purchase, **When** the agent reports back, **Then** it shows minimal confirmation (product name + success indicator)
- **Given** a failed purchase, **When** the agent reports back, **Then** it shows a clear error message explaining the failure (e.g., "Vending machine unavailable", "Product not found", "Payment failed")

---

### Story 2.6: Graceful Error Handling

**As** an AI Engineer, **I want** the agent to handle failures gracefully, **so that** I understand what went wrong without debugging raw errors.

**Acceptance Criteria:**
- **Given** the vending machine is unreachable, **When** the agent attempts to connect, **Then** it reports "Vending machine unavailable at [URL]"
- **Given** an unknown product is requested, **When** the agent receives a 404, **Then** it reports "Product not found" and lists available products
- **Given** a payment failure, **When** AgentCore reports an error, **Then** the agent reports the payment failure reason clearly

---

## Epic 3: Observability

### Story 3.1: Agent Reasoning Traces

**As** an AI Engineer, **I want** to see traces of the agent's reasoning loops and tool calls in Grafana, **so that** I can understand and debug agent behavior.

**Acceptance Criteria:**
- **Given** the agent executes a task, **When** I check Grafana Tempo, **Then** I see spans for: agent reasoning, tool calls (HTTP requests), and overall execution
- **Given** OpenInference instrumentation is active, **When** traces are exported, **Then** they follow OpenInference semantic conventions for AI spans
- **Given** Grafana credentials are configured in `.env`, **When** the agent runs, **Then** traces are exported via OTLP automatically

---

### Story 3.2: Payment Transaction Tracing

**As** an AI Engineer, **I want** to see payment transactions as distinct spans in traces, **so that** I can observe the x402 flow end-to-end.

**Acceptance Criteria:**
- **Given** a payment is executed, **When** I view the trace, **Then** I can see the 402 response, payment execution, and retry as separate spans
- **Given** a complete purchase flow, **When** I view the trace, **Then** I can follow the full journey: discover → attempt → 402 → pay → retry → success

---

### Story 3.3: Metrics and Logs

**As** an AI Engineer, **I want** metrics and structured logs exported to Grafana, **so that** I have a complete observability picture.

**Acceptance Criteria:**
- **Given** the agent runs, **When** metrics are collected, **Then** token usage, latency, and payment amounts are exported to Grafana Mimir
- **Given** the agent runs, **When** logs are generated, **Then** structured logs are exported to Grafana Loki via OTLP

---

## Epic 4: Infrastructure & Dev Experience

### Story 4.1: Local Development Workflow

**As** an AI Engineer, **I want** to run both components locally for development, **so that** I can iterate quickly without deploying.

**Acceptance Criteria:**
- **Given** the project is cloned, **When** I run `uvicorn` for the API, **Then** the vending machine is accessible at localhost
- **Given** the API is running locally, **When** I run the agent CLI, **Then** it can interact with the local vending machine
- **Given** `.env` is configured, **When** I run either component, **Then** it picks up configuration automatically

---

### Story 4.2: CDK Infrastructure Deployment

**As** an AI Engineer, **I want** all infrastructure defined as CDK (Python), **so that** I can deploy and tear down the entire stack reliably.

**Acceptance Criteria:**
- **Given** CDK is configured, **When** I run `cdk deploy`, **Then** the vending machine Lambda + API Gateway are created in ap-southeast-2
- **Given** CDK is configured, **When** I run `cdk deploy`, **Then** the AgentCore Runtime configuration is provisioned
- **Given** a deployed stack, **When** I run `cdk destroy`, **Then** all resources are cleaned up

---

### Story 4.3: AgentCore Runtime Deployment

**As** an AI Engineer, **I want** the agent deployed to AgentCore Runtime, **so that** it runs in a managed, serverless environment with built-in observability.

**Acceptance Criteria:**
- **Given** CDK infrastructure is deployed, **When** the agent is launched on AgentCore Runtime, **Then** it can receive and process purchase requests
- **Given** the agent is running on AgentCore, **When** it executes, **Then** built-in observability (CloudWatch + ADOT) is active alongside Grafana export
- **Given** the agent is on AgentCore, **When** it needs to make payments, **Then** the AgentCore Payments plugin works natively

---

## Story-Persona Mapping

| Story | Primary Persona | Secondary Persona |
|-------|----------------|-------------------|
| 1.1–1.4 | Vending Machine API | AI Agent |
| 2.1–2.2 | AI Engineer | AI Agent |
| 2.3–2.6 | AI Agent | AI Engineer |
| 3.1–3.3 | AI Engineer | — |
| 4.1–4.3 | AI Engineer | — |

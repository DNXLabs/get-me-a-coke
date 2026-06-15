# Unit of Work — Story Map: Get Me a Coke

## Story-to-Unit Mapping

| Story | Title | Unit | Notes |
|-------|-------|------|-------|
| 1.1 | Product Catalog Discovery | Unit 1: Vending Machine | GET /products endpoint |
| 1.2 | x402 Payment Terms Response | Unit 1: Vending Machine | 402 response with payment terms |
| 1.3 | Payment Acceptance and Dispensing | Unit 1: Vending Machine | X-PAYMENT header validation + dispense |
| 1.4 | Error Handling | Unit 1: Vending Machine | 404 for unknown products |
| 2.1 | Single-Shot Purchase | Unit 2: Agent | CLI single-shot mode |
| 2.2 | Interactive REPL Mode | Unit 2: Agent | CLI interactive mode |
| 2.3 | Autonomous Product Discovery | Unit 2: Agent | Agent queries catalog |
| 2.4 | Autonomous Payment Execution | Unit 2: Agent | AgentCore Payments plugin handles 402 |
| 2.5 | Purchase Confirmation | Unit 2: Agent | Minimal result output |
| 2.6 | Graceful Error Handling | Unit 2: Agent | Clear error messages |
| 3.1 | Agent Reasoning Traces | Unit 3: Observability | StrandsAgentsToOpenInferenceProcessor |
| 3.2 | Payment Transaction Tracing | Unit 3: Observability | Payment spans in traces |
| 3.3 | Metrics and Logs | Unit 3: Observability | OTLP export to Grafana |
| 4.1 | Local Development Workflow | Unit 4: Infrastructure | uvicorn + CLI scripts |
| 4.2 | CDK Infrastructure Deployment | Unit 4: Infrastructure | Lambda + API Gateway + AgentCore |
| 4.3 | AgentCore Runtime Deployment | Unit 4: Infrastructure | AgentCore Runtime config in CDK |

## Coverage Verification

| Unit | Stories Assigned | Total | Coverage |
|------|-----------------|-------|----------|
| Unit 1: Vending Machine | 1.1, 1.2, 1.3, 1.4 | 4 | ✅ Complete |
| Unit 2: Agent | 2.1, 2.2, 2.3, 2.4, 2.5, 2.6 | 6 | ✅ Complete |
| Unit 3: Observability | 3.1, 3.2, 3.3 | 3 | ✅ Complete |
| Unit 4: Infrastructure | 4.1, 4.2, 4.3 | 3 | ✅ Complete |
| **Total** | | **16** | ✅ All stories assigned |

## Cross-Unit Stories

| Story | Primary Unit | Secondary Unit | Integration Point |
|-------|-------------|----------------|-------------------|
| 2.3 (Product Discovery) | Unit 2: Agent | Unit 1: Vending Machine | Agent calls GET /products |
| 2.4 (Payment Execution) | Unit 2: Agent | Unit 1: Vending Machine | Agent calls POST /purchase, gets 402, pays, retries |
| 3.1 (Reasoning Traces) | Unit 3: Observability | Unit 2: Agent | Observability instruments agent spans |
| 3.2 (Payment Tracing) | Unit 3: Observability | Unit 2: Agent | Payment spans captured from agent execution |
| 4.2 (CDK Deployment) | Unit 4: Infrastructure | Units 1, 2 | CDK deploys both services |

## Unassigned Stories

None — all 16 stories are assigned to exactly one primary unit.

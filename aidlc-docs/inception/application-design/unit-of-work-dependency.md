# Unit of Work Dependencies: Get Me a Coke

## Dependency Matrix

| Unit | Depends On | Dependency Type | Blocking? |
|------|-----------|-----------------|-----------|
| 1. Vending Machine API | None | — | No (can start immediately) |
| 2. AI Agent | Unit 1 (for integration tests) | Runtime (HTTP) | Soft (unit tests don't need it) |
| 3. Observability | Unit 2 (instruments agent) | Build-time (import) | Soft (can develop telemetry module independently) |
| 4. Infrastructure | Units 1, 2 (deploys them) | Deployment-time | Soft (CDK skeleton can be built early) |

## Dependency Graph

```
+-------------------+
| Unit 1            |
| Vending Machine   |  <-- No dependencies, start first
+--------+----------+
         |
         | HTTP (integration test)
         v
+--------+----------+
| Unit 2            |
| AI Agent          |  <-- Needs Unit 1 URL for integration tests
+--------+----------+
         |
         | import (build-time)
         v
+--------+----------+
| Unit 3            |
| Observability     |  <-- Instruments Unit 2
+-------------------+

+-------------------+
| Unit 4            |
| Infrastructure    |  <-- Develops in parallel, deploys Units 1+2
+-------------------+
```

## Development Order

### Recommended Sequence (with parallelism)

```
Time -->

Unit 1 (Vending Machine): [=====dev=====][=test=]
Unit 4 (Infrastructure):  [===skeleton===][====fill====]
Unit 2 (Agent):                    [=====dev=====][=test=]
Unit 3 (Observability):                    [===dev===][=test=]
```

**Wave 1** (can start simultaneously):
- Unit 1: Vending Machine API (fully independent)
- Unit 4: Infrastructure skeleton (CDK stacks with placeholder resources)

**Wave 2** (after Unit 1 has basic endpoints):
- Unit 2: AI Agent (can unit-test independently, integration test needs Unit 1)
- Unit 3: Observability (can develop telemetry module independently)
- Unit 4: Fill in CDK with real Lambda/API Gateway config

**Wave 3** (integration):
- Integration testing: Agent → local Vending Machine
- CDK deployment: Deploy all stacks

## Shared Resources

| Resource | Used By | Location |
|----------|---------|----------|
| `.env` configuration | Units 2, 3 | Project root |
| Pydantic models (Product, PaymentTerms) | Units 1, 2 (agent parses API responses) | `src/vending_machine/models.py` (agent uses raw JSON, no shared import needed) |
| `pyproject.toml` | Units 1, 2, 3 | Project root |

**Note**: No shared code library needed. The agent interacts with the vending machine via HTTP (JSON), so there's no build-time coupling between Units 1 and 2. Each unit can be developed and tested independently.

## Integration Points

| From | To | Interface | Contract |
|------|-----|-----------|----------|
| Agent (Unit 2) | Vending Machine (Unit 1) | HTTP REST | `GET /products` → JSON list; `POST /purchase/{id}` → 402 or 200 |
| Agent (Unit 2) | Observability (Unit 3) | Python import | `from observability.telemetry import configure_telemetry` |
| Infrastructure (Unit 4) | Vending Machine (Unit 1) | Deployment | Lambda function packaging |
| Infrastructure (Unit 4) | Agent (Unit 2) | Deployment | AgentCore Runtime configuration |

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Agent can't reach vending machine locally | Unit 1 runs on localhost:8000 via uvicorn; agent config points there |
| AgentCore Payments not available locally | Mock payment flow in unit tests; real AgentCore only in integration/deployed |
| CDK drift from application code | Develop CDK in parallel, validate with `cdk synth` frequently |
| Nemotron Nano not in existing IAM role | Create project-specific role (don't modify foundation stacks) |

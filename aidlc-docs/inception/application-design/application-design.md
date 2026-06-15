# Application Design: Get Me a Coke

## Overview

A 4-component system implementing autonomous agent-to-service commerce via x402 payment protocol.

## Architecture

```
+-------------------+     HTTP      +---------------------+
|   AI Engineer     | ------------> |      Agent          |
|   (CLI)           | <------------ |   (Strands SDK)     |
+-------------------+   results     +----------+----------+
                                               |
                                    +----------+----------+
                                    |                     |
                              HTTP (REST)           SDK (internal)
                                    |                     |
                                    v                     v
                        +-----------+---+    +-----------+--------+
                        | Vending       |    | AgentCore Payments  |
                        | Machine API   |    | (402 auto-handler)  |
                        | (FastAPI)     |    +---------------------+
                        +---------------+              |
                                                       v
                                              +--------+---------+
                                              |    Bedrock       |
                                              | (Nemotron Nano)  |
                                              +------------------+

                        Agent exports telemetry:
                        +------------------+
                        |  Grafana Cloud   |
                        | Tempo/Mimir/Loki |
                        +------------------+
```

## Components Summary

| # | Component | Type | Framework | Deployment |
|---|-----------|------|-----------|------------|
| 1 | Vending Machine API | REST API | FastAPI + Mangum | Lambda + API Gateway |
| 2 | Agent | Autonomous AI Agent | Strands SDK | AgentCore Runtime |
| 3 | Observability | Instrumentation layer | OTel + OpenInference | Embedded in agent |
| 4 | Infrastructure | IaC | AWS CDK (Python) | CloudFormation |

## Key Design Decisions

1. **No custom payment tool** — AgentCore Payments plugin handles 402 detection and payment transparently. The agent only needs `http_request` from `strands_tools`.

2. **Stateless vending machine** — Product catalog is hardcoded (2-3 products). No database, no persistence. Each request is independent.

3. **Observability is passive** — StrandsInstrumentor auto-creates spans. No manual span creation needed for MVP.

4. **Single `pyproject.toml`** — Monorepo with both components in `src/`. CDK infrastructure in `infra/` with its own dependencies.

5. **Deployment order** — Vending machine deploys first (independent). Agent needs vending machine URL as config.

## Cross-References

- **Detailed components**: [components.md](components.md)
- **Method signatures**: [component-methods.md](component-methods.md)
- **Service interactions**: [services.md](services.md)
- **Dependencies**: [component-dependency.md](component-dependency.md)
- **Requirements**: [../requirements/requirements.md](../requirements/requirements.md)
- **User Stories**: [../user-stories/stories.md](../user-stories/stories.md)

# Business Logic Model: Observability

## Overview

The observability unit provides telemetry wiring that transforms Strands agent spans into OpenInference format and exports them to Grafana Cloud. It's a configuration/initialization module — no complex business logic, just correct setup of the OTel pipeline.

## Core Flow

```
Agent starts
      |
      v
configure_telemetry() called
      |
      v
1. Create TracerProvider
2. Add StrandsAgentsToOpenInferenceProcessor (transforms spans)
3. Add BatchSpanProcessor with OTLPSpanExporter (exports to Grafana)
4. Set as global TracerProvider
5. (Optional) Configure MeterProvider + LoggerProvider
      |
      v
Strands SDK automatically emits spans to global provider
      |
      v
Spans flow: Strands → OpenInference Processor → OTLP Exporter → Grafana
```

## Business Processes

### 1. Telemetry Initialization
- **Input**: Grafana credentials from .env (endpoint, instance ID, API token)
- **Process**: Configure OTel providers with correct processor ordering
- **Output**: Global TracerProvider set, ready to receive spans
- **Business Rule**: Must be called BEFORE agent is created (provider must be global first)

### 2. Span Transformation
- **Input**: Strands native OTel spans (agent reasoning, tool calls, model invocations)
- **Process**: StrandsAgentsToOpenInferenceProcessor transforms to OpenInference semantic conventions
- **Output**: Spans with OpenInference attributes (ai.agent, ai.tool, ai.llm semantics)
- **Business Rule**: Processor ordering matters — OpenInference processor BEFORE OTLP exporter

### 3. Span Export
- **Input**: Transformed OpenInference spans
- **Process**: BatchSpanProcessor batches and exports via OTLP/HTTP to Grafana
- **Output**: Spans visible in Grafana Tempo
- **Business Rule**: Export is async/non-blocking (fire-and-forget, doesn't affect agent performance)

## Configuration

| Parameter | Source | Required |
|-----------|--------|----------|
| GRAFANA_OTLP_ENDPOINT | .env | Yes |
| GRAFANA_INSTANCE_ID | .env | Yes |
| GRAFANA_API_TOKEN | .env | Yes |
| Service name | Hardcoded ("get-me-a-coke-agent") | — |

## What Gets Traced (Automatic via StrandsAgentsToOpenInferenceProcessor)

| Span Type | OpenInference Semantic | Content |
|-----------|----------------------|---------|
| Agent invocation | `AGENT` | Full agent execution (root span) |
| Model call | `LLM` | Bedrock inference (model, tokens, latency) |
| Tool call | `TOOL` | http_request execution (URL, status, duration) |
| Agent reasoning cycle | `CHAIN` | Plan-act-observe loop iterations |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Grafana credentials missing | Log warning, skip telemetry setup (agent still works) |
| OTLP export fails | BatchSpanProcessor retries silently, drops after max retries |
| Invalid endpoint | Export fails silently (non-blocking) |

**Key principle**: Observability failures MUST NOT crash the agent. Telemetry is best-effort.

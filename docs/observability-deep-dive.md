# Observability in Agentic AI: Upgrading OpenTelemetry with OpenInference

**A Deep Dive into AI Observability for AWS Runtime Environments with Grafana**

---

## Executive Summary

Traditional observability tools designed for microservices are insufficient for AI agents. While OpenTelemetry provides excellent infrastructure for distributed tracing, it lacks semantic understanding of LLM operations, agent reasoning chains, and AI-specific performance characteristics.

**OpenInference** extends OpenTelemetry's semantic conventions specifically for AI workloads, enabling:
- Visibility into LLM reasoning chains and tool execution
- Tracking of token usage, latency, and cost per generation
- Correlation between user intent and multi-step agent behaviors
- Detection of hallucinations, prompt injection, and safety issues

This document explores the integration of OpenInference with AWS runtime environments (Lambda, ECS, AgentCore Runtime) and Grafana's emerging AI observability capabilities.

---

## Table of Contents

1. [The AI Observability Gap](#the-ai-observability-gap)
2. [OpenTelemetry Fundamentals](#opentelemetry-fundamentals)
3. [OpenInference: AI-Specific Semantic Conventions](#openinference-ai-specific-semantic-conventions)
4. [Evaluation: The Fourth Pillar of AI Observability](#evaluation-the-fourth-pillar-of-ai-observability)
5. [Human-in-the-Loop Approval Gates](#human-in-the-loop-approval-gates)
6. [AWS Runtime Considerations](#aws-runtime-considerations)
7. [Grafana AI Observability Stack](#grafana-ai-observability-stack)
8. [Implementation Guide](#implementation-guide)
9. [Real-World Example: Get Me a Coke](#real-world-example-get-me-a-coke)
10. [Best Practices and Pitfalls](#best-practices-and-pitfalls)
11. [Future Directions](#future-directions)

---

## The AI Observability Gap

### What Traditional Observability Misses

Traditional APM tools capture:
- HTTP request/response cycles
- Database queries
- Cache hits/misses
- Error rates and latency percentiles

**But traditional observability falls short for LLMs** because their outputs are non-deterministic and their internal "reasoning" processes are opaque. Standard OpenTelemetry is excellent for tracking latency and error rates in traditional software, but it lacks the specialized semantic conventions needed to capture the complex, non-deterministic behaviors of AI workloads.

| Traditional Service | AI Agent |
|-------------------|----------|
| Single request → single response | Multiple reasoning steps → multiple LLM calls |
| Deterministic execution path | Non-deterministic reasoning chains |
| Latency measured in milliseconds | Latency measured in seconds (token generation) |
| Fixed resource cost | Variable cost (token usage) |
| Failures are binary (success/error) | Failures are spectrum (hallucination, refusal, partial success) |

### What We Need to Observe in AI Systems

1. **Reasoning Chains** - How did the agent decide to take action X?
2. **Tool Execution Flows** - Which tools were called, in what order, with what parameters?
3. **LLM Generation Metadata** - Token counts, temperature, top-p, stop sequences
4. **Prompt Engineering** - What was the actual prompt sent to the model?
5. **Response Quality** - Did the model hallucinate? Did it refuse? Was output parseable?
6. **Cost Attribution** - Token usage per conversation, per user, per feature
7. **Safety Events** - Prompt injection attempts, PII leakage, policy violations
8. **Evaluation Metrics** - Relevancy, Faithfulness, Correctness, Hallucination Rates

### The Era of AI FinOps (2026)

As we enter 2026, **FinOps for AI** has become critical. Organizations need to:
- Track OpenAI/Bedrock API costs in real-time
- Attribute spend across models, features, and users
- Implement guardrail monitoring to prevent runaway costs
- Optimize model selection (GPT-4 vs Claude vs Gemini) based on cost-per-task
- Monitor token-to-task ratios to identify inefficient prompts

---

## OpenTelemetry Fundamentals

### Three Pillars of Observability

OpenTelemetry standardizes collection and export of:

#### 1. **Traces** - Distributed request flows
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("agent.run") as span:
    span.set_attribute("user.id", "thiago")
    span.set_attribute("agent.goal", "buy_coke")
    # Agent execution happens here
```

**Spans** represent units of work. A trace is a tree of spans showing parent-child relationships.

#### 2. **Metrics** - Aggregated measurements
```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
request_counter = meter.create_counter("agent.requests")
latency_histogram = meter.create_histogram("agent.latency")

request_counter.add(1, {"status": "success"})
latency_histogram.record(1.2, {"model": "claude-sonnet-4.6"})
```

#### 3. **Logs** - Structured event records
```python
import logging
from opentelemetry._logs import set_logger_provider

logger = logging.getLogger(__name__)
logger.info("Agent started", extra={"user.id": "thiago", "trace_id": trace_id})
```

### The OTLP Protocol

**OpenTelemetry Protocol (OTLP)** is a vendor-neutral wire format for telemetry data:
- Supports gRPC and HTTP/protobuf
- Single endpoint for traces, metrics, and logs
- Grafana, Datadog, New Relic, Honeycomb all accept OTLP

```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint="https://otlp-gateway.grafana.net/v1/traces",
    headers={"Authorization": "Basic <credentials>"}
)
```

### What OpenTelemetry Doesn't Know About

Standard OTel semantic conventions define attributes for:
- HTTP requests: `http.method`, `http.status_code`, `http.url`
- Databases: `db.system`, `db.statement`, `db.operation`
- RPC calls: `rpc.service`, `rpc.method`, `rpc.system`

But there are **no standard attributes** for:
- LLM model invocation
- Token usage and cost
- Prompt content and templates
- Agent reasoning steps
- Tool execution in agentic flows

**This is the gap OpenInference fills.**

---

## OpenInference: AI-Specific Semantic Conventions

### Overview: The OpenInference Foundation

**OpenInference is a vendor-agnostic standard built directly on top of OpenTelemetry (OTel).** Created by Arize AI, it establishes a shared language to capture telemetry across different models and providers, transforming the "black box" of generative AI into a transparent, cost-efficient, and secure production environment.

While standard OTel is great for tracking latency and error rates in traditional software, OpenInference extends it by introducing specialized semantic conventions designed specifically for:
- LLM invocations and generation metadata
- Embeddings generation
- Retrieval operations (RAG)
- Agent reasoning and multi-step tool use
- Prompt templates and variables

### Key Span Kinds: Hierarchical Agent Tracing

**Agentic workflows rarely involve a single API call; they require hierarchical tracing to map out recursive reasoning.** OpenInference manages this using a specialized attribute called `openinference.span.kind` to categorize different operations into a visual tree.

The primary span kinds include:

```python
# OpenInference Span Kinds (via openinference.span.kind attribute)
AGENT      # Top-level span: autonomous entity's overall objective and final outcome
CHAIN      # Sequence of steps: high-level workflow context
TOOL       # External function execution: captures tool.name, tool.parameters, results
LLM        # Model invocation: the "leaves" of the trace tree
RETRIEVAL  # Vector search / RAG retrieval operations
EMBEDDING  # Embedding generation spans
```

**Critical insight**: By nesting TOOL and LLM spans inside an overarching AGENT span, developers can easily drill down to see if a failure occurred due to:
- A bad tool parameter
- An LLM reasoning error
- The initial system prompt
- Or retrieval quality in RAG pipelines

This hierarchical structure is what separates AI observability from traditional APM.

### Semantic Conventions: Granular Attribute Mapping

OpenInference defines specific categories and attributes to attach to telemetry spans. **To handle complex data, it heavily relies on JSON formatting.**

#### Model Metadata
```python
# Identify the specific model version
span.set_attribute("llm.model_name", "claude-sonnet-4.6")
span.set_attribute("llm.provider", "anthropic")
```

#### Usage Metrics: The Foundation of Cost Tracking
```python
# Precisely track token consumption for cost attribution
span.set_attribute("llm.token_count.prompt", 150)
span.set_attribute("llm.token_count.completion", 75)
span.set_attribute("llm.token_count.total", 225)

# Cost attribution (derived from token counts)
span.set_attribute("llm.cost.prompt", 0.00045)  # $3/MTok input
span.set_attribute("llm.cost.completion", 0.00113)  # $15/MTok output
span.set_attribute("llm.cost.total", 0.00158)
```

**Key insight**: Usage metrics enable real-time FinOps tracking. Query platforms can aggregate `llm.token_count.total` by user, feature, or conversation to identify cost optimization opportunities.

#### Inference Parameters
```python
# Track hyperparameters for reproducibility and optimization
span.set_attribute("llm.invocation_parameters", json.dumps({
    "temperature": 0.7,
    "max_tokens": 1024,
    "top_p": 0.9
}))
```

#### Input/Output Context
```python
# Store conversation history and prompts (JSON-formatted)
span.set_attribute("llm.input_messages", json.dumps([
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is 2+2?"}
]))

span.set_attribute("llm.output_messages", json.dumps([
    {"role": "assistant", "content": "2+2 equals 4"}
]))
```

**⚠️ Privacy Warning**: Raw prompts and completions often contain sensitive PII. Ensure content capture is strictly opt-in and utilize redaction processors at the collector level before data leaves your network.

### Semantic Conventions for Tool Spans

**Tool spans capture the execution of external functions**, showing how the agent interacts with its environment. This is critical for debugging agentic workflows.

```python
span.set_attribute("tool.name", "get_weather")
span.set_attribute("tool.description", "Fetches current weather for a location")

# JSON-formatted parameters show exact input
span.set_attribute("tool.parameters", json.dumps({
    "location": "Sydney",
    "units": "celsius"
}))

# Capture returned values for debugging
span.set_attribute("tool.output", json.dumps({
    "temperature": 22,
    "conditions": "sunny"
}))

# Track exceptions if the tool fails
# span.set_status(StatusCode.ERROR, "API timeout")
```

**Why this matters**: When an agent fails, you need to know:
- Which tool was called?
- What parameters were passed?
- What did the tool return?
- Did the LLM correctly interpret the tool's output?

Tool spans answer all four questions.

### Agent Reasoning Chain Example

A typical agentic trace with OpenInference conventions shows the hierarchical structure:

```
[AGENT] agent.run (user: "What's the weather in Sydney?")
  ├─ [LLM] claude-sonnet-4.6 (tokens: 150/50, cost: $0.0008)
  │   └─ Output: "I'll check the weather for you"
  ├─ [TOOL] get_weather(location="Sydney")
  │   └─ Result: {"temp": 22, "conditions": "sunny"}
  └─ [LLM] claude-sonnet-4.6 (tokens: 180/40, cost: $0.0009)
      └─ Output: "It's 22°C and sunny in Sydney"
```

Each span carries rich context:
- **AGENT span**: Overall objective, user input, final output, agent role (system prompt)
- **CHAIN spans** (if present): Individual reasoning steps or sub-tasks, retry status
- **LLM spans**: Full prompt, completion, token counts, hyperparameters
- **TOOL spans**: Tool name, JSON parameters, returned values, exceptions

### Evaluation Metrics: Qualitative Monitoring

Beyond latency and token counts, OpenInference establishes a system for **qualitative monitoring** with these evaluation metrics:

| Metric | Definition | Use Case |
|--------|-----------|----------|
| **Relevancy** | How relevant is the output to the input query? | Detect off-topic responses |
| **Faithfulness** | Is the output grounded in provided context? | RAG hallucination detection |
| **Correctness** | Is the output factually accurate? | Compare against ground truth |
| **Hallucination Rate** | % of responses containing ungrounded claims | Safety and quality monitoring |

These metrics are typically calculated post-hoc by evaluator LLMs or human reviewers, then attached to spans as attributes for aggregation in dashboards.

---

## Evaluation: The Fourth Pillar of AI Observability

Traditional observability has three pillars: **Traces, Metrics, and Logs**. AI systems require a **fourth pillar: Evaluation**.

### Why Evaluation Matters

Unlike traditional software where failures are binary (HTTP 500 = failure, 200 = success), **AI systems fail along a spectrum**:

| Failure Type | HTTP Status | User Impact | Detection Method |
|-------------|-------------|-------------|------------------|
| Model timeout | 500 | High | Standard APM |
| Hallucination | 200 | High | Evaluation |
| Off-topic response | 200 | Medium | Evaluation |
| Verbose output | 200 | Low | Token metrics + Evaluation |
| Refusal (overly cautious) | 200 | Medium | Evaluation |

**Traditional observability sees a 200 response as success, but the user received a hallucinated answer.** Evaluation closes this gap.

### Types of Evaluation

#### 1. **Automated Evaluation (LLM-as-Judge)**

Use an evaluator LLM to score outputs on quality dimensions:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def evaluate_response(user_query: str, agent_response: str, context: str) -> dict:
    """Evaluate agent response using LLM-as-judge pattern."""
    
    # Use a powerful model (GPT-4, Claude Opus) as evaluator
    evaluator_prompt = f"""
    Evaluate this AI agent response on the following criteria:
    
    User Query: {user_query}
    Agent Response: {agent_response}
    Retrieved Context: {context}
    
    Score each on a scale of 1-5:
    1. Relevancy: Is the response relevant to the query?
    2. Faithfulness: Is the response grounded in the provided context?
    3. Correctness: Is the response factually accurate?
    4. Completeness: Does the response fully answer the query?
    
    Return JSON: {{"relevancy": X, "faithfulness": X, "correctness": X, "completeness": X, "hallucination_detected": boolean}}
    """
    
    scores = evaluator_llm(evaluator_prompt)  # Call evaluator model
    
    return scores

# Attach evaluation scores to the trace
with tracer.start_as_current_span("agent.evaluate") as span:
    scores = evaluate_response(query, response, context)
    
    span.set_attribute("eval.relevancy", scores["relevancy"])
    span.set_attribute("eval.faithfulness", scores["faithfulness"])
    span.set_attribute("eval.correctness", scores["correctness"])
    span.set_attribute("eval.completeness", scores["completeness"])
    span.set_attribute("eval.hallucination_detected", scores["hallucination_detected"])
```

**Key insight**: Attach evaluation scores as span attributes so they can be queried and aggregated in Grafana/Tempo.

#### 2. **Human Evaluation (Spot Checks)**

Sample a subset of conversations for human review:

```python
import random

def should_sample_for_review(trace_id: str) -> bool:
    """Sample 5% of traces for human review."""
    return random.random() < 0.05

if should_sample_for_review(trace_id):
    # Flag for human review
    span.set_attribute("eval.requires_human_review", True)
    span.set_attribute("eval.review_reason", "random_sample")
```

Store flagged traces in a review queue (e.g., database, S3) where human reviewers can:
- Rate response quality (1-5 stars)
- Mark hallucinations
- Provide corrected responses

#### 3. **Ground Truth Comparison (Test Sets)**

For known queries with expected outputs, calculate exact match or similarity scores:

```python
from difflib import SequenceMatcher

def calculate_similarity(ground_truth: str, actual_output: str) -> float:
    """Calculate similarity between expected and actual output."""
    return SequenceMatcher(None, ground_truth, actual_output).ratio()

# For test dataset
for test_case in test_dataset:
    response = agent(test_case["query"])
    similarity = calculate_similarity(test_case["expected_output"], response)
    
    # Store as metric
    span.set_attribute("eval.ground_truth_similarity", similarity)
    span.set_attribute("eval.test_case_id", test_case["id"])
```

### Observability Integration: Traces + Evaluation

**Pattern**: Run evaluation asynchronously after the user response is sent, then attach scores to the existing trace.

```python
from opentelemetry import trace
from opentelemetry.trace import get_current_span
import threading

def handle_user_query(query: str) -> str:
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("agent.query") as span:
        span.set_attribute("user.query", query)
        
        # Generate response
        response = agent(query)
        span.set_attribute("agent.response", response)
        
        # Capture trace_id for async evaluation
        trace_id = span.get_span_context().trace_id
        
        # Send response to user immediately
        # (Don't make user wait for evaluation)
        
        # Async evaluation (attach to existing trace)
        threading.Thread(
            target=async_evaluate,
            args=(trace_id, query, response)
        ).start()
        
        return response

def async_evaluate(trace_id: int, query: str, response: str):
    """Run evaluation asynchronously and attach to existing trace."""
    tracer = trace.get_tracer(__name__)
    
    # Create child span linked to original trace
    ctx = trace.set_span_in_context(trace.NonRecordingSpan(
        trace.SpanContext(trace_id=trace_id, span_id=0, is_remote=True, trace_flags=trace.TraceFlags(0x01))
    ))
    
    with tracer.start_as_current_span("agent.evaluate", context=ctx) as eval_span:
        scores = evaluate_response(query, response, context="")
        
        eval_span.set_attribute("eval.relevancy", scores["relevancy"])
        eval_span.set_attribute("eval.faithfulness", scores["faithfulness"])
        eval_span.set_attribute("eval.hallucination_detected", scores["hallucination_detected"])
```

### Querying Evaluation Data in Grafana

Once evaluation scores are attached to spans, query them with TraceQL:

```traceql
# Find all traces where hallucination was detected
{ span.eval.hallucination_detected = true }

# Find low-quality responses (relevancy < 3)
{ span.eval.relevancy < 3 }

# Calculate average faithfulness score by model
{ name = "agent.evaluate" }
| select(avg(span.eval.faithfulness) as avg_faithfulness) by (resource.ai.model.id)

# Find traces that failed both automated and human eval
{ span.eval.faithfulness < 3 && span.eval.human_rating < 3 }
```

### Evaluation Metrics Dashboard

Create a Grafana dashboard tracking:

| Metric | Query | Target |
|--------|-------|--------|
| Hallucination Rate | `count(eval.hallucination_detected = true) / count(*)` | < 2% |
| Avg Relevancy Score | `avg(eval.relevancy)` | > 4.0 |
| Avg Faithfulness Score | `avg(eval.faithfulness)` | > 4.0 |
| Human Review Queue Size | `count(eval.requires_human_review = true && eval.human_reviewed = false)` | < 100 |

**Alert example**:

```yaml
- alert: HighHallucinationRate
  expr: |
    rate(eval_hallucination_detected_total[1h]) > 0.02
  annotations:
    summary: "Hallucination rate above 2% in last hour"
    description: "{{ $value }}% of responses were flagged as hallucinations"
```

### Continuous Improvement Loop

Evaluation enables a continuous improvement cycle:

```
1. Agent generates response
     ↓
2. Response sent to user (low latency)
     ↓
3. Async evaluation (LLM-as-judge + human spot checks)
     ↓
4. Scores attached to trace as span attributes
     ↓
5. Grafana dashboard shows quality trends
     ↓
6. Low-quality traces trigger alerts
     ↓
7. Engineers investigate root cause (prompt, model, retrieval)
     ↓
8. Fix deployed (new prompt, different model, improved RAG)
     ↓
9. Evaluation scores improve (measurable in dashboard)
```

**Key principle**: Evaluation transforms AI quality from subjective ("feels better") to objective ("faithfulness improved from 3.2 to 4.5").

---

## Human-in-the-Loop Approval Gates

For high-stakes agent actions (financial transactions, data deletion, external API calls), **human approval is non-negotiable**. Observability must prove that HITL gates are enforced.

### Why HITL Matters

AI agents can:
- Execute irreversible actions (delete data, send emails, transfer money)
- Misinterpret user intent
- Hallucinate parameters for tool calls
- Bypass safety checks due to prompt injection

**HITL approval gates** ensure:
1. Human reviews the action before execution
2. Human can veto the action
3. Every approval/denial is audited (who, when, what)

### HITL Patterns

#### Pattern 1: Conversational Approval (Two-Step Flow)

Agent shows a quote/preview and waits for explicit user confirmation.

**From get-me-a-coke project**:

```python
# System prompt excerpt
SYSTEM_PROMPT = """
PURCHASE FLOW (mandatory):
1. Use list_products to show what's available
2. Use get_purchase_quote to get the price
3. Show the quote to the user and ASK for explicit approval
4. ONLY if the user says yes/approve/confirm, call execute_purchase
5. If the user says no/cancel/decline, do NOT call execute_purchase

NEVER call execute_purchase without showing the quote and getting user approval first.
"""

# Agent execution
def run_agent(user_query: str) -> str:
    agent = create_agent()
    
    with tracer.start_as_current_span("agent.run") as span:
        span.set_attribute("user.query", user_query)
        span.set_attribute("hitl.required", True)
        
        response = agent(user_query)
        
        # Check if agent is asking for approval
        if "approve" in response.lower() or "confirm" in response.lower():
            span.set_attribute("hitl.approval_requested", True)
            span.set_attribute("hitl.pending_action", "execute_purchase")
        
        return response
```

**Observability**: Trace shows whether agent requested approval and whether user granted it.

#### Pattern 2: Tool-Level Enforcement (Gatekeeper Tool)

The `execute_purchase` tool refuses to run unless a prior `get_purchase_quote` call exists in the trace.

```python
from opentelemetry import trace
import logging

logger = logging.getLogger(__name__)

def execute_purchase(product_id: str) -> dict:
    """Execute purchase ONLY if quote was previously fetched (HITL gate)."""
    
    tracer = trace.get_tracer(__name__)
    current_span = trace.get_current_span()
    
    # Check if get_purchase_quote was called in this trace
    # (In production, query trace backend or check in-memory state)
    quote_exists = check_quote_in_trace(current_span.get_span_context().trace_id, product_id)
    
    with tracer.start_as_current_span("tool.execute_purchase") as span:
        span.set_attribute("tool.name", "execute_purchase")
        span.set_attribute("tool.parameters", json.dumps({"product_id": product_id}))
        span.set_attribute("hitl.gate_enforced", True)
        
        if not quote_exists:
            # HITL gate violation - reject
            span.set_attribute("hitl.gate_passed", False)
            span.set_attribute("hitl.rejection_reason", "no_prior_quote")
            
            logger.error(
                "HITL gate violation: execute_purchase called without prior quote",
                extra={
                    "product_id": product_id,
                    "trace_id": hex(current_span.get_span_context().trace_id),
                    "user_id": get_current_user_id()
                }
            )
            
            raise PermissionError("Cannot execute purchase without prior quote approval")
        
        # Quote exists - proceed with purchase
        span.set_attribute("hitl.gate_passed", True)
        result = perform_purchase(product_id)
        
        # Audit log
        logger.info(
            "Purchase executed with HITL approval",
            extra={
                "product_id": product_id,
                "user_id": get_current_user_id(),
                "trace_id": hex(current_span.get_span_context().trace_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return result
```

**Key insight**: Tool-level enforcement prevents prompt injection attacks. Even if a malicious prompt tricks the agent into calling `execute_purchase` directly, the tool refuses.

#### Pattern 3: Explicit Approval API

For non-conversational agents (scheduled, batch, API-driven), implement an explicit approval API:

```python
from enum import Enum
from datetime import datetime, timedelta

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"

# In-memory store (use database in production)
approval_requests: dict[str, dict] = {}

def request_approval(
    action: str,
    parameters: dict,
    user_id: str,
    trace_id: int
) -> str:
    """Create an approval request and return approval_id."""
    
    approval_id = str(uuid4())
    
    approval_requests[approval_id] = {
        "action": action,
        "parameters": parameters,
        "user_id": user_id,
        "trace_id": trace_id,
        "status": ApprovalStatus.PENDING,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    # Log to observability
    with tracer.start_as_current_span("hitl.approval_requested") as span:
        span.set_attribute("approval.id", approval_id)
        span.set_attribute("approval.action", action)
        span.set_attribute("approval.user_id", user_id)
        span.set_attribute("approval.parameters", json.dumps(parameters))
    
    return approval_id

def check_approval(approval_id: str) -> ApprovalStatus:
    """Check if approval was granted."""
    
    request = approval_requests.get(approval_id)
    if not request:
        return ApprovalStatus.DENIED
    
    # Check expiration
    if datetime.utcnow() > request["expires_at"]:
        request["status"] = ApprovalStatus.EXPIRED
    
    return request["status"]

def execute_with_approval(approval_id: str) -> dict:
    """Execute action only if approved."""
    
    status = check_approval(approval_id)
    
    with tracer.start_as_current_span("hitl.execute_with_approval") as span:
        span.set_attribute("approval.id", approval_id)
        span.set_attribute("approval.status", status.value)
        
        if status != ApprovalStatus.APPROVED:
            span.set_attribute("hitl.gate_passed", False)
            raise PermissionError(f"Action not approved: {status.value}")
        
        span.set_attribute("hitl.gate_passed", True)
        
        # Execute the action
        request = approval_requests[approval_id]
        result = execute_action(request["action"], request["parameters"])
        
        # Audit log
        logger.info(
            "Action executed with HITL approval",
            extra={
                "approval_id": approval_id,
                "action": request["action"],
                "user_id": request["user_id"],
                "trace_id": hex(request["trace_id"])
            }
        )
        
        return result
```

**Usage**:

```python
# Step 1: Agent requests approval
approval_id = request_approval(
    action="execute_purchase",
    parameters={"product_id": "coke", "price": "$0.01"},
    user_id="thiago",
    trace_id=current_trace_id
)

# Step 2: Send approval request to user (email, Slack, web UI)
send_approval_notification(user_id="thiago", approval_id=approval_id)

# Step 3: User approves via web UI or API
# POST /api/approvals/{approval_id}/approve

# Step 4: Agent checks approval and executes
result = execute_with_approval(approval_id)
```

### Observability for HITL Gates

**What to track**:

1. **Approval Request Rate**: How often does the agent ask for approval?
   ```promql
   rate(hitl_approval_requested_total[1h])
   ```

2. **Approval Grant Rate**: What % of requests are approved?
   ```promql
   rate(hitl_approval_granted_total[1h]) / rate(hitl_approval_requested_total[1h])
   ```

3. **Gate Violations**: How often does agent try to bypass HITL?
   ```promql
   rate(hitl_gate_violation_total[1h])
   ```

4. **Pending Approval Queue**: How many approvals are waiting?
   ```promql
   sum(hitl_approval_pending)
   ```

**TraceQL queries**:

```traceql
# Find all traces where HITL gate was violated
{ span.hitl.gate_passed = false }

# Find traces where purchase executed with approval
{ span.tool.name = "execute_purchase" && span.hitl.gate_passed = true }

# Find traces where user denied approval
{ span.hitl.approval_status = "denied" }
```

### Audit Trail Requirements

**Every HITL action must be auditable**:

```python
# Structured audit log
logger.info(
    "HITL approval granted",
    extra={
        "event": "hitl.approval_granted",
        "approval_id": approval_id,
        "user_id": user_id,
        "approver_id": approver_id,  # Who approved (may differ from requester)
        "action": "execute_purchase",
        "parameters": {"product_id": "coke", "price": "$0.01"},
        "trace_id": hex(trace_id),
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent")
    }
)
```

**Audit requirements (compliance/governance)**:

| Field | Required | Purpose |
|-------|----------|---------|
| `user_id` | Yes | Who requested the action? |
| `approver_id` | Yes | Who approved it? (may be different) |
| `action` | Yes | What action was approved? |
| `parameters` | Yes | What were the exact parameters? |
| `timestamp` | Yes | When was it approved? |
| `trace_id` | Yes | Full trace for forensic analysis |
| `ip_address` | Recommended | Detect unauthorized access |
| `decision_reason` | Recommended | Why was it approved/denied? |

**Query audit logs in Grafana Loki**:

```logql
# Find all approvals by user in last 30 days
{app="agent"} |= "hitl.approval_granted" | json | user_id="thiago" | line_format "{{.timestamp}} {{.action}}"

# Find all denials
{app="agent"} |= "hitl.approval_denied"

# Find approvals for high-value purchases
{app="agent"} |= "hitl.approval_granted" | json | parameters_price > "$1.00"
```

### HITL Best Practices

1. **Make HITL mandatory for high-stakes actions** in system prompt and tool-level enforcement
2. **Log every approval/denial** with full context (who, what, when, why)
3. **Set expiration times** on approval requests (e.g., 24 hours)
4. **Track gate violations** (agent attempting to bypass HITL) as security events
5. **Dashboard HITL metrics** (request rate, approval rate, pending queue size)
6. **Alert on anomalies** (sudden spike in requests, high denial rate, gate violations)

### Proof of HITL Compliance

For regulated industries (finance, healthcare), you need to **prove** HITL is enforced:

**Compliance report query (TraceQL + Loki)**:

```sql
-- All purchases in Q1 2026
SELECT 
  trace_id,
  user_id,
  action,
  parameters,
  hitl.approval_requested,
  hitl.approval_granted,
  hitl.gate_passed,
  timestamp
FROM traces
WHERE 
  action = "execute_purchase"
  AND timestamp BETWEEN '2026-01-01' AND '2026-03-31'
ORDER BY timestamp DESC
```

**Compliance check**:
- Every `execute_purchase` must have `hitl.approval_requested = true`
- Every `execute_purchase` must have `hitl.gate_passed = true`
- Every `execute_purchase` must have a corresponding audit log entry

If any row fails these checks, HITL was bypassed → compliance violation.

---

## AWS Runtime Considerations

### Runtime Options for AI Agents

| Runtime | Use Case | Observability Integration |
|---------|----------|---------------------------|
| **AWS Lambda** | Event-driven, short-lived agents (<15min) | ADOT Lambda layer + OTLP export |
| **ECS Fargate** | Long-running agents, stateful sessions | ADOT sidecar container + OTLP export |
| **ECS EC2** | High-throughput, cost-optimized | ADOT DaemonSet + OTLP export |
| **AgentCore Runtime** | Managed agent platform (Bedrock) | Built-in ADOT + CloudWatch, custom OTLP export |

### AWS Distro for OpenTelemetry (ADOT)

**ADOT** is AWS's distribution of OpenTelemetry with:
- Pre-configured X-Ray exporter (AWS-native tracing)
- CloudWatch Metrics and Logs exporters
- Lambda layer for zero-code instrumentation
- ECS task definition templates

**Limitation**: ADOT's default exporters don't understand OpenInference conventions. X-Ray will store the spans but won't parse `llm.token_count.*` attributes into meaningful visualizations.

**Solution**: Dual-export strategy:
1. Export to X-Ray (for AWS-native correlation with Lambda/ECS metrics)
2. Export to Grafana Cloud via OTLP (for AI-specific dashboards)

### Lambda + OpenInference Pattern

```python
# Lambda handler with OpenInference instrumentation
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.strands_agents import StrandsAgentsToOpenInferenceProcessor

# Initialize TracerProvider BEFORE importing agent code
provider = TracerProvider()

# OpenInference processor transforms Strands spans → OpenInference conventions
provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())

# Export to Grafana Cloud
provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(
        endpoint=os.environ["GRAFANA_OTLP_ENDPOINT"] + "/v1/traces",
        headers={"Authorization": f"Basic {os.environ['GRAFANA_AUTH']}"}
    )
))

trace.set_tracer_provider(provider)

# NOW import and run agent
from agent import create_agent

def handler(event, context):
    agent = create_agent()
    response = agent(event["query"])
    return {"statusCode": 200, "body": response}
```

**Key insight**: The OpenInference processor must be added BEFORE the OTLP exporter so spans are transformed before export.

### AgentCore Runtime + Custom OTLP Export

AgentCore Runtime (Bedrock's managed agent platform) has built-in ADOT that exports to CloudWatch. To also send to Grafana:

```python
# src/observability/telemetry.py (from get-me-a-coke project)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from openinference.instrumentation.strands_agents import StrandsAgentsToOpenInferenceProcessor

def configure_telemetry(grafana_endpoint: str, grafana_auth: str):
    provider = TracerProvider()
    
    # Add OpenInference processor first
    provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())
    
    # Add Grafana OTLP exporter
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=f"{grafana_endpoint}/v1/traces", headers={"Authorization": f"Basic {grafana_auth}"})
    ))
    
    trace.set_tracer_provider(provider)
```

This coexists with AgentCore's built-in ADOT — spans are sent to **both** CloudWatch (via ADOT) and Grafana (via custom export).

### ECS + Distributed Tracing: Local Collector Pattern

For ECS-based agents (or any AWS runtime), use the **OpenTelemetry Collector or Grafana Alloy** as a local telemetry router. This pattern provides several benefits:

**Why use a local collector?**
- **Process and batch data** before sending to Grafana (reduces OTLP requests)
- **Redact sensitive PII from prompts** at the collector level (before data leaves your network)
- **Handle authentication** at the collector, not in application code
- **Route to multiple backends** (X-Ray + Grafana) from a single OTLP endpoint

**Architecture**:

```yaml
# ECS task definition (excerpt)
containerDefinitions:
  - name: agent
    image: my-agent:latest
    environment:
      # Send unauthenticated OTLP to local collector
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: http://localhost:4318
      - name: OTEL_SERVICE_NAME
        value: my-agent
    
  - name: otel-collector
    image: public.ecr.aws/aws-observability/aws-otel-collector:latest
    # OR: grafana/alloy:latest
    command: ["--config=/etc/otel-config.yaml"]
    environment:
      - name: GRAFANA_OTLP_ENDPOINT
        valueFrom: secretsmanager:grafana-otlp-endpoint
      - name: GRAFANA_AUTH
        valueFrom: secretsmanager:grafana-auth-token
```

**Collector configuration** (handles PII redaction and authenticated export):

```yaml
# otel-config.yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  
  # Redact PII before export
  redaction:
    allow_all_keys: false
    blocked_values:
      - "\\b\\d{3}-\\d{2}-\\d{4}\\b"  # SSN pattern

exporters:
  # Export to X-Ray for AWS-native correlation
  awsxray:
    region: us-east-1
  
  # Export to Grafana for AI dashboards
  otlphttp:
    endpoint: ${GRAFANA_OTLP_ENDPOINT}
    headers:
      Authorization: Basic ${GRAFANA_AUTH}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [redaction, batch]
      exporters: [awsxray, otlphttp]
```

The ADOT collector/Grafana Alloy acts as a proxy:
- Receives OTLP from agent container (port 4318)
- Redacts PII and batches spans
- Exports to X-Ray for AWS-native tracing
- Exports to Grafana for AI-specific dashboards

**For high-volume production environments, it is recommended to send unauthenticated OTLP data to a local OpenTelemetry Collector or Grafana Alloy first.** This local collector can process, redact sensitive PII from prompts, and batch the data before handling the authenticated export to Grafana Cloud.

---

## Grafana AI Observability Stack

### The Grafana OTLP Gateway: Single Pane of Glass

Grafana provides a **unified "single pane of glass"** for monitoring LLM costs, quality, and performance by leveraging its core **LGTM stack** (Loki, Grafana, Tempo, Mimir).

Grafana Cloud provides a unified OTLP endpoint for all three signals:

```
Base: https://otlp-gateway-prod-us-east-0.grafana.net/otlp

Traces:  /otlp/v1/traces
Metrics: /otlp/v1/metrics
Logs:    /otlp/v1/logs
```

**Authentication**: `Authorization: Basic base64(instance_id:api_token)`

You can configure this using standard OpenTelemetry environment variables without hardcoding credentials:

```bash
# Set OTLP endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp-gateway-prod-us-east-0.grafana.net/otlp"

# Set authentication header
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic $(echo -n 'instance_id:api_token' | base64)"
```

### Storage Backends: The LGTM Stack

| Signal | Grafana Backend | Query Language | Optimized For |
|--------|----------------|----------------|---------------|
| Traces | **Tempo** | TraceQL | Distributed tracing, hierarchical agent spans |
| Metrics | **Mimir** (Prometheus) | PromQL | Time-series aggregation, token cost dashboards |
| Logs | **Loki** | LogQL | Log aggregation, conversational event search |

All three are open-source projects (AGPL) with managed Grafana Cloud option.

#### Grafana Tempo: Scalable AI Trace Storage

Tempo acts as the **highly scalable, cost-effective storage backend for distributed tracing**. Key features for AI observability:

- **Native OTLP Support**: Ingests hierarchical agent and LLM spans seamlessly
- **Metrics-Generator**: Derives Rate, Error, and Duration (RED) metrics directly from traces, enabling real-time performance dashboards even if your application only emits span data
- **Cost-Efficient**: Object storage backend (S3, GCS) dramatically reduces storage costs vs traditional trace databases

#### Grafana Mimir: Long-Term Metrics Storage

Mimir provides **horizontally scalable, long-term storage for OpenTelemetry and Prometheus metrics**. For AI workloads, it stores:

- Time to First Token (TTFT)
- Inter-token latency
- Total token throughput
- Cost per conversation, per user, per feature
- Request rates and error percentages

#### Grafana Loki: Conversational Log Search

Loki handles **logs and raw conversational events**. Key advantages:

- **Cost-Effective at Scale**: Only indexes metadata labels, storing actual log chunks in object storage
- **Trace Correlation**: When correlated with Tempo traces (via `trace_id`), you can examine the exact prompts and tool outputs that led to a specific model failure or latency spike
- **PII Redaction**: Can be configured to strip sensitive data before storage

### GenAI Semantic Conventions Support (NEW)

As of **Grafana 11.4** (Q1 2025), Tempo has native support for OpenTelemetry's **GenAI semantic conventions** (experimental):

```
gen_ai.request.model
gen_ai.response.finish_reasons
gen_ai.usage.input_tokens
gen_ai.usage.output_tokens
```

**Compatibility**: OpenInference conventions (`llm.model_name`, `llm.token_count.prompt`) map cleanly to GenAI conventions. Grafana recognizes both.

### Key AI Observability Metrics

#### Token-to-Task Ratio: Efficiency Metric

**Token-to-Task Ratio** measures how many tokens an agent consumes to complete a single task. It's calculated as:

```
Token-to-Task Ratio = Total Tokens Used / Number of Tasks Completed
```

A high ratio indicates:
- Verbose or redundant prompts
- Inefficient tool-calling loops (agent retrying same tool multiple times)
- Hallucination causing excessive back-and-forth

**Example calculation from traces**:

```traceql
# Query Tempo for token efficiency
{ name = "agent.run" } 
| select(
    sum(span.llm.token_count.total) as total_tokens,
    count() as task_count
  )
| rate(total_tokens / task_count)
```

Use this metric to:
- Identify expensive conversation patterns
- Compare prompt engineering strategies
- Detect agent loops or stuck states

### AI-Specific Grafana Features

#### 1. **LLM Trace Visualization**

Grafana's Tempo UI automatically detects LLM spans and renders:
- **Token usage pie chart** (prompt vs completion)
- **Cost breakdown** per span
- **Prompt/completion diff view** (before/after)

To enable: Ensure spans have `span.kind = LLM` and `llm.token_count.*` attributes.

#### 2. **Agent Flow Diagrams**

Tempo's **Service Graph** feature visualizes agent tool execution flows:

```
[Agent] → [LLM] → [Tool: get_weather] → [LLM] → [User]
```

Each edge shows:
- Request rate (requests/sec)
- P50/P95/P99 latency
- Error rate

#### 3. **Cost Attribution Dashboards**

PromQL queries over token usage metrics:

```promql
# Cost per user (last 24h)
sum by (user_id) (
  rate(llm_token_count_total{signal="completion"}[24h]) * 0.000015
)

# Most expensive agent tools
topk(10,
  sum by (tool_name) (llm_cost_total)
)
```

#### 4. **Anomaly Detection for Hallucinations**

Use **Grafana Machine Learning** to detect:
- Sudden spikes in output token usage (verbose hallucinations)
- High refusal rates (prompt injection defense)
- Latency outliers (model throttling)

Example alert:

```yaml
# Alert: Excessive token usage
- alert: AgentTokenSpike
  expr: |
    rate(llm_token_count_completion[5m]) > 
    avg_over_time(rate(llm_token_count_completion[5m])[1h]) * 3
  annotations:
    summary: "Agent {{ $labels.agent_name }} token usage 3x above baseline"
```

### Grafana Explore + TraceQL for AI Debugging

**TraceQL** is Tempo's query language for spans. AI-specific queries:

```traceql
# Find all traces where agent called "execute_purchase" tool
{ span.tool.name = "execute_purchase" }

# Find expensive generations (>$0.01)
{ span.llm.cost.total > 0.01 }

# Find slow reasoning chains (>10s)
{ name = "agent.run" && duration > 10s }

# Find traces with errors in LLM spans
{ span.kind = "LLM" && status = "error" }

# Find multi-tool agent flows
{ span.kind = "TOOL" } | count() > 3
```

These queries power dashboards and alerts.

---

## Implementation Guide

### Step-by-Step: Instrumenting a Strands Agent

**Critical Principle**: The instrumentation pattern for Strands Agents relies on **"wrapping" the framework's internal classes and methods BEFORE any Strands Agent objects are instantiated**. While general LLM instrumentors only capture raw interactions with the model, this specialized wrapping captures the framework's high-level intent by mapping internal objects directly to OpenInference attributes and span kinds.

This creates a **highly detailed, async-aware hierarchical trace** using Python's `contextvars` to maintain context across asynchronous boundaries.

#### 1. Install Dependencies

```bash
pip install \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp \
  openinference-instrumentation-strands-agents \
  opentelemetry-instrumentation-httpx
```

**Package note**: The `openinference-instrumentation-strands-agents` library provides the `StrandsInstrumentor` for automatic instrumentation.

#### 2. Configure Telemetry (Before Agent Creation)

**CRITICAL REQUIREMENT**: Always initialize your instrumentor and configure your `TracerProvider` and `MeterProvider` in your application **BEFORE** importing or instantiating any AI clients or agent objects. Without this, your SDK will silently drop data into a no-op state.

```python
# src/observability/telemetry.py
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.strands_agents import StrandsAgentsToOpenInferenceProcessor

def configure_telemetry(service_name: str):
    # Service metadata (Resource Attributes)
    # These distinguish between environments (staging vs production) and versions
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "0.1.0",
        "deployment.environment": "production",
        "ai.model.id": "claude-sonnet-4.6",
        "ai.model.provider": "anthropic.bedrock"
    })
    
    # Create TracerProvider
    provider = TracerProvider(resource=resource)
    
    # CRITICAL: Add OpenInference processor BEFORE OTLP exporter
    # This transforms raw Strands spans into OpenInference-compliant spans
    provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())
    
    # Add OTLP exporter for Grafana (BatchSpanProcessor for efficient batching)
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "") + "/v1/traces"
    otlp_headers = {
        "Authorization": f"Basic {os.environ.get('GRAFANA_AUTH_BASIC', '')}"
    }
    
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=otlp_endpoint, headers=otlp_headers)
    ))
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    
    # Auto-instrument httpx for distributed tracing (trace context propagation)
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    HTTPXClientInstrumentor().instrument()
```

**Resource Attributes** are essential for filtering data in observability platforms like Arize Phoenix or Grafana. They allow you to:
- Filter traces by environment (`deployment.environment = "production"`)
- Compare performance across versions (`service.version`)
- Track which model generated a specific trace (`ai.model.id`)

#### 3. Enable Latest GenAI Semantic Conventions

```python
# Add this BEFORE configuring telemetry
os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = "gen_ai_latest_experimental"
```

This opts into:
- `gen_ai.request.model` instead of `llm.model_name`
- `gen_ai.usage.input_tokens` instead of `llm.token_count.prompt`

Grafana recognizes both but prefers GenAI conventions.

#### 4. Initialize Strands Instrumentor

**CRITICAL**: Initialize the `StrandsInstrumentor` BEFORE importing any Strands classes.

```python
# Initialize StrandsInstrumentor to wrap framework internals
from openinference.instrumentation.strands_agents import StrandsInstrumentor

StrandsInstrumentor().instrument()
```

This activation wraps Strands' internal classes to emit OpenInference-compliant spans automatically. It must be called before any `Agent` objects are created.

#### 5. Create Agent with Instrumentation

```python
# src/agent/agent.py
from strands import Agent
from strands.models.bedrock import BedrockModel

def create_agent():
    model = BedrockModel(
        model_id="anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="us-east-1"
    )
    
    return Agent(
        model=model,
        system_prompt="You are a helpful assistant",
        tools=[tool1, tool2, tool3]
    )

# Agent automatically emits OTel spans via Strands SDK
# StrandsInstrumentor wrapping ensures spans have OpenInference attributes
# OpenInference processor transforms them further before OTLP export
```

**What gets traced automatically**:
- **Agent spans (AGENT)**: Top-level span with system prompt, user input, final output
- **Task spans (CHAIN/INTERNAL)**: Nested spans for reasoning steps, including retry status
- **Tool spans (TOOL)**: External function calls with JSON parameters and results
- **LLM spans (LLM)**: Model invocations with token counts and hyperparameters

#### 6. Run Agent

```python
# main.py
from observability.telemetry import configure_telemetry
from openinference.instrumentation.strands_agents import StrandsInstrumentor

# Step 1: Configure telemetry FIRST (TracerProvider, MeterProvider)
configure_telemetry("my-agent")

# Step 2: Initialize StrandsInstrumentor BEFORE importing Agent
StrandsInstrumentor().instrument()

# Step 3: NOW safe to import and create agent
from agent import create_agent
agent = create_agent()

# Step 4: Run agent (spans automatically exported to Grafana)
response = agent("What's the weather in Sydney?")
print(response)
```

**Initialization order is critical**:
1. Configure OTel providers (TracerProvider, MeterProvider) first
2. Initialize StrandsInstrumentor to wrap framework classes
3. Import and create Agent objects
4. Run agent - spans flow through the pipeline automatically

#### 6. Verify in Grafana

Navigate to **Explore → Tempo** and search:

```traceql
{ service.name = "my-agent" }
```

You should see:
- **CHAIN span**: `agent.run` with full conversation
- **LLM spans**: Each model invocation with token counts
- **TOOL spans**: Tool executions with parameters and results

---

## Real-World Example: Get Me a Coke

The **get-me-a-coke** project demonstrates production-grade AI observability for a Strands agent on AWS, including:
- OpenInference instrumentation for LLM and tool tracing
- Human-in-the-loop approval gates for purchases
- Audit logging for compliance
- Dual export to CloudWatch and Grafana Cloud

### Architecture

```
User → AgentCore Runtime (Strands Agent)
           ↓
       System Prompt (HITL requirement) → Audit Logs
           ↓
       [Tools: list_products, get_purchase_quote, execute_purchase, wallet_pay]
           ↓
       HITL Gate: execute_purchase refuses without prior quote
           ↓
       [OpenInference Instrumentation]
           ↓
       [Dual Export: CloudWatch + Grafana Cloud]
```

**Key features**:
- Two-step purchase flow with mandatory human approval
- Tool-level enforcement (not just prompt-based)
- Every purchase logged with user_id, timestamp, context
- Observability proves HITL compliance

### Key Implementation Details

#### 1. Telemetry Configuration

From `src/observability/telemetry.py`:

```python
def configure_telemetry(
    grafana_otlp_endpoint: str,
    grafana_instance_id: str,
    grafana_api_token: str,
    service_name: str = "get-me-a-coke-agent"
):
    # Enable latest GenAI semantic conventions
    os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = (
        "gen_ai_latest_experimental,"
        "gen_ai_tool_definitions,"
        "gen_ai_use_latest_invocation_tokens"
    )
    
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "0.1.0",
        "deployment.environment": "dev",
        "ai.model.id": "nvidia.nemotron-nano-3-30b",
        "ai.model.provider": "aws.bedrock"
    })
    
    provider = TracerProvider(resource=resource)
    
    # OpenInference processor FIRST
    provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())
    
    # Grafana OTLP export SECOND
    headers = build_grafana_auth_headers(grafana_instance_id, grafana_api_token)
    exporter = OTLPSpanExporter(
        endpoint=f"{grafana_otlp_endpoint}/v1/traces",
        headers=headers
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    
    trace.set_tracer_provider(provider)
```

**Why this ordering matters**: The OpenInference processor transforms raw Strands spans into OpenInference-compliant spans. If the OTLP exporter runs first, Grafana receives raw spans without AI semantic conventions.

#### 2. Agent Instrumentation

From `src/agent/agent.py`:

```python
from strands import Agent
from strands.models.bedrock import BedrockModel

def create_agent(config: AgentConfig) -> Agent:
    model = BedrockModel(
        model_id=config.bedrock_model_id,  # nvidia.nemotron-nano-3-30b
        region_name=config.aws_region
    )
    
    return Agent(
        model=model,
        system_prompt=get_system_prompt(config),
        tools=[list_products, get_purchase_quote, execute_purchase, wallet_get_balance]
    )
```

**No explicit instrumentation code** — Strands SDK emits OTel spans automatically, and the OpenInference processor handles transformation.

#### 3. Distributed Tracing Across Services

The agent calls external APIs (vending machine, wallet service). To propagate trace context:

```python
# Instrument httpx for automatic trace propagation
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
HTTPXClientInstrumentor().instrument()

# Now all httpx calls automatically send W3C traceparent header
import httpx
async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://vending-machine.example.com/purchase/coke"
    )
    # Trace context propagated automatically
```

The vending machine API (FastAPI) also instruments with OpenTelemetry:

```python
# src/vending_machine/app.py
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

@app.post("/purchase/{product_id}")
async def purchase(product_id: str):
    # This span is automatically linked to parent agent span
    return {"status": "dispensed"}
```

Result: **End-to-end trace** from user query → agent reasoning → tool execution → API call → response.

#### 5. Human-in-the-Loop Approval Gate

The project demonstrates **conversational approval + tool-level enforcement**:

**System prompt enforces two-step flow**:
```python
SYSTEM_PROMPT = """
PURCHASE FLOW (mandatory):
1. Use list_products to show what's available
2. Use get_purchase_quote to get the price
3. Show the quote to the user and ASK for explicit approval
4. ONLY if the user says yes/approve/confirm, call execute_purchase
5. If the user says no/cancel/decline, do NOT call execute_purchase

NEVER call execute_purchase without showing the quote and getting user approval first.
This is an audited action — every purchase is logged with user identity and timestamp.
"""
```

**Tool-level enforcement** (from `src/agent/tools/vending_machine.py`):

```python
# Tool state tracking (simplified)
conversation_state = {}

def get_purchase_quote(product_id: str) -> dict:
    """Get quote for product (step 1 of HITL flow)."""
    quote = fetch_quote(product_id)
    
    # Store quote in conversation state
    conversation_state["last_quote"] = {
        "product_id": product_id,
        "price": quote["price"],
        "timestamp": datetime.utcnow()
    }
    
    with tracer.start_as_current_span("tool.get_purchase_quote") as span:
        span.set_attribute("tool.name", "get_purchase_quote")
        span.set_attribute("hitl.quote_provided", True)
    
    return quote

def execute_purchase(product_id: str) -> dict:
    """Execute purchase ONLY if quote was previously shown (HITL gate)."""
    
    with tracer.start_as_current_span("tool.execute_purchase") as span:
        span.set_attribute("tool.name", "execute_purchase")
        span.set_attribute("hitl.gate_enforced", True)
        
        # Check if quote exists
        last_quote = conversation_state.get("last_quote")
        
        if not last_quote or last_quote["product_id"] != product_id:
            span.set_attribute("hitl.gate_passed", False)
            raise PermissionError("Cannot purchase without showing quote first")
        
        # Check quote age (expire after 5 minutes)
        if datetime.utcnow() - last_quote["timestamp"] > timedelta(minutes=5):
            span.set_attribute("hitl.gate_passed", False)
            raise PermissionError("Quote expired, please request new quote")
        
        span.set_attribute("hitl.gate_passed", True)
        
        # Execute purchase
        result = perform_purchase(product_id, last_quote["price"])
        
        # Audit log
        logger.info(
            "Purchase executed with HITL approval",
            extra={
                "product_id": product_id,
                "price": last_quote["price"],
                "user_id": get_current_user(),
                "trace_id": hex(span.get_span_context().trace_id)
            }
        )
        
        return result
```

**Observability proof of HITL**:

Query Tempo for compliance report:
```traceql
# All purchases must have prior quote in same trace
{ span.tool.name = "execute_purchase" }
| select(
    span.hitl.gate_passed as gate_passed,
    span.trace_id as trace_id
  )
| filter(gate_passed = false)  # Should be empty!
```

If this query returns results, HITL was bypassed → investigate immediately.

#### 4. Metrics and Logs

The project also exports metrics and structured logs:

```python
# Metrics export to Grafana Mimir
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

metric_exporter = OTLPMetricExporter(
    endpoint=f"{grafana_otlp_endpoint}/v1/metrics",
    headers=grafana_headers
)
meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[PeriodicExportingMetricReader(metric_exporter)]
)
metrics.set_meter_provider(meter_provider)

# Logs export to Grafana Loki
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

log_exporter = OTLPLogExporter(
    endpoint=f"{grafana_otlp_endpoint}/v1/logs",
    headers=grafana_headers
)
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

# Attach to Python logging
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)
```

This creates a **unified observability stack** in Grafana: traces, metrics, and logs all correlated by `trace_id`.

---

## Best Practices and Pitfalls

### Best Practices

#### 1. Initialize Early: Configure Providers Before Importing AI Clients

**Always initialize your instrumentor and TracerProvider/MeterProvider BEFORE importing or instantiating any AI clients or agent objects.**

```python
# ✅ CORRECT
configure_telemetry()              # Set up TracerProvider, MeterProvider
StrandsInstrumentor().instrument()  # Wrap framework classes
agent = create_agent()              # Now safe to create agent

# ❌ WRONG - Agent emits spans before telemetry is ready
agent = create_agent()
configure_telemetry()
```

Without proper initialization, your SDK will silently drop data into a no-op state with no error messages.

#### 2. Add OpenInference Processor Before OTLP Exporter

**Span processors execute in order.** The OpenInference processor must transform spans before they're exported.

```python
# ✅ CORRECT - Transform first, then export
provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(...)))

# ❌ WRONG - Spans exported before transformation
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(...)))
provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())
```

#### 3. Use Semantic Resource Attributes for Environment Filtering

Resource attributes distinguish between environments and enable powerful filtering in Grafana.

```python
resource = Resource.create({
    "service.name": "my-agent",
    "service.version": "1.2.3",
    "deployment.environment": "production",  # Filter by environment
    "ai.model.id": "claude-sonnet-4.6",      # Track which model
    "ai.model.provider": "anthropic.bedrock",
    "aws.region": "us-east-1"
})
```

These appear as filterable tags in Grafana dashboards and Tempo queries.

#### 4. Configure Tail Sampling to Control Costs

**Configure your collector to use tail sampling** to store 100% of error or low-quality traces, but only a small percentage of successful ones, keeping storage costs manageable.

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces (adjust based on volume)
sampler = TraceIdRatioBased(rate=0.1)
provider = TracerProvider(sampler=sampler, resource=resource)
```

For production environments with high volume, implement intelligent sampling:
- 100% of error traces
- 100% of slow traces (>5s)
- 10% of successful traces

This is typically done at the OpenTelemetry Collector level, not in-app.

#### 5. Sanitize PII from Prompts and Ensure Content Capture is Opt-In

**Raw prompts and completions often contain sensitive PII.** Ensure content capture is strictly opt-in and utilize redaction processors at the collector level before data leaves your network.

```python
# ⚠️ DANGER - PII in trace
span.set_attribute("llm.input_messages", json.dumps([
    {"role": "user", "content": f"My SSN is {user_ssn}"}
]))

# ✅ CORRECT - Redact PII before exporting
from observability.sanitize import redact_pii

sanitized_prompt = redact_pii(prompt)
span.set_attribute("llm.input_messages", sanitized_prompt)
```

**Best practice**: Configure PII redaction at the **OpenTelemetry Collector** level, not in application code. This ensures consistent redaction across all services.

#### 6. Flush Telemetry on Lambda Shutdown

Lambda freezes the execution environment — without explicit flush, buffered spans may not export.

```python
import atexit
from opentelemetry import trace

def flush_telemetry():
    trace.get_tracer_provider().shutdown()

atexit.register(flush_telemetry)
```

### Common Pitfalls

#### 1. Silent Data Loss: Missing Instrumentor Initialization

**Symptom**: No spans appear in Grafana, but application runs without errors.

**Cause**: Failed to initialize `StrandsInstrumentor()` before creating agents, or missing a required dependency.

**Fix**: Verify initialization order and check that `openinference-instrumentation-strands-agents` is installed:

```python
# Verify package is installed
pip list | grep openinference

# Initialize BEFORE importing Agent
StrandsInstrumentor().instrument()
```

**Silent data loss** is the most insidious failure mode - your application works fine but produces no telemetry.

#### 2. Data Privacy Leaks: PII in Prompts

**Symptom**: Sensitive user data (SSN, emails, health info) stored in trace spans.

**Cause**: Raw prompts and completions contain PII, exported to observability platform without redaction.

**Critical**: This is a **compliance and security violation**. Never export raw prompts without PII redaction.

**Fix**: Configure PII redaction at the OpenTelemetry Collector level:

```yaml
# otel-collector-config.yaml
processors:
  redaction:
    allow_all_keys: false
    blocked_values:
      - "\\b\\d{3}-\\d{2}-\\d{4}\\b"  # SSN
      - "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"  # Email
```

#### 3. Cardinality Explosion: Unbounded Metric Labels

**Symptom**: Metrics backend (Mimir/Prometheus) crashes or rejects data; query performance degrades.

**Cause**: Using unbounded values as metric labels (full prompt text, unique conversation IDs, raw JSON).

**Never use unbounded values as metric labels.** This will quickly overwhelm and crash your metrics backend.

**Fix**: Use low-cardinality labels only:

```python
# ❌ BAD - High cardinality (millions of unique values)
span.set_attribute("user.email", user_email)
span.set_attribute("conversation.id", uuid4())
span.set_attribute("prompt.text", full_prompt)

# ✅ GOOD - Low cardinality
span.set_attribute("user.tier", "premium")  # Limited values
span.set_attribute("model.family", "claude-3")
span.set_attribute("tool.name", "get_weather")  # Fixed set of tools
```

#### 4. Missing Trace Context Propagation

**Symptom**: Agent span and downstream API span appear as separate traces in Grafana.

**Cause**: httpx/requests not instrumented for W3C trace context propagation.

**Fix**: Instrument HTTP clients to propagate `traceparent` header:

```python
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
HTTPXClientInstrumentor().instrument()

# Now all httpx calls automatically propagate trace context
```

#### 5. Rate Limiting on OTLP Export

**Symptom**: "429 Too Many Requests" errors in logs; spans dropped.

**Cause**: Grafana Cloud free tier has rate limits (e.g., 50 spans/sec).

**Fix**: Use `BatchSpanProcessor` to reduce request frequency:

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(
    exporter,
    max_queue_size=2048,       # Buffer more spans
    schedule_delay_millis=5000, # Batch every 5s
    max_export_batch_size=512   # Send 512 spans per request
)
```

Or upgrade to Grafana Cloud Pro, or self-host Grafana + Tempo.

#### 6. Missing OTLP Endpoint Verification

**Symptom**: Application runs but no data in Grafana; no obvious errors.

**Cause**: Incorrect OTLP endpoint URL or authentication headers.

**Fix**: Verify OTLP connectivity before deploying:

```bash
# Test OTLP endpoint with curl
curl -X POST https://otlp-gateway.grafana.net/otlp/v1/traces \
  -H "Authorization: Basic $(echo -n 'instance_id:token' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans": []}'

# Should return 200 OK or 400 (empty body)
```

---

## Complementary Observability Tools

### OpenLIT: Turnkey Instrumentation SDK

**OpenLIT** is an open-source SDK that simplifies OpenInference instrumentation with a single initialization call:

```python
import openlit

openlit.init(
    otlp_endpoint="https://otlp-gateway.grafana.net/otlp",
    otlp_headers={"Authorization": "Basic <credentials>"}
)

# Automatically instruments LangChain, LlamaIndex, OpenAI SDK, Anthropic SDK, etc.
```

**Key features**:
- **Automatic instrumentation** for 30+ LLM frameworks
- **Guardrail monitoring** for prompt injection, PII leakage, toxic content
- **Built-in dashboards** for Grafana (pre-built JSON)
- **Metrics collection** (token usage, latency, error rates)

Use OpenLIT when you want turnkey instrumentation without manually configuring TracerProvider and processors.

### Grafana Sigil: AI Observability SDK

**Grafana Sigil** (preview) is Grafana's proprietary SDK for AI observability, designed to work alongside OpenTelemetry:

```python
from sigil_sdk import Client, ClientConfig
from sigil_sdk.config import AuthConfig, GenerationExportConfig

auth_config = AuthConfig(
    mode="bearer",
    tenant_id="your-tenant-id",
    bearer_token="your-token"
)

client_config = ClientConfig(
    generation_export=GenerationExportConfig(
        endpoint="https://sigil.grafana.net",
        protocol="http",
        auth=auth_config
    )
)

sigil_client = Client(config=client_config)
```

**Why use Sigil alongside OTel?**
- **LLM-specific visualizations** (not available in standard Tempo UI)
- **Automatic evaluation metrics** (relevancy, faithfulness, hallucination detection)
- **Cost optimization insights** (suggests prompt compression, model downgrading)
- **Real-time guardrails** (blocks toxic outputs before they reach users)

Sigil complements OpenTelemetry by adding AI-native analysis on top of standard traces.

## Future Directions

### 1. Unified GenAI Semantic Conventions

OpenTelemetry is standardizing GenAI conventions (currently experimental). Once stable, expect:
- Native support across APM vendors (Datadog, New Relic, Honeycomb)
- Deprecated OpenInference conventions (migrate to `gen_ai.*`)
- Richer LLM span visualization (tool calling, structured outputs)

**Migration path**: OpenInference will likely provide a compatibility layer.

### 2. Grafana AI Assistant Integration

Grafana is building **Grafana AI Assistant** (preview):
- Natural language query over traces: "Show me all expensive agent runs yesterday"
- Automatic anomaly explanations: "Why did token usage spike at 3pm?"
- Suggested optimizations: "This prompt is redundant, trim 30%"

Powered by LLMs querying the observability backend.

### 3. Agent-Specific SLOs

**Service Level Objectives** for AI agents:
- **Latency SLO**: "95% of agent runs complete in <5s"
- **Cost SLO**: "Average cost per conversation <$0.10"
- **Quality SLO**: "Tool execution success rate >98%"

Grafana's **SLO** plugin will support AI-specific metrics.

### 4. Federated Tracing for Multi-Agent Systems

As agent architectures become multi-agent (orchestrator + specialist agents), traces span multiple services:

```
User → Orchestrator Agent
          ├→ Research Agent → [Web Search Tool]
          ├→ Data Agent → [SQL Query Tool]
          └→ Synthesis Agent → [LLM]
```

Grafana's **Trace to Metrics** and **Trace to Logs** features enable cross-service debugging.

### 5. Cost Optimization Insights

Grafana dashboards will surface:
- "Top 10 most expensive prompts" (identify optimization targets)
- "Token usage by feature" (cost attribution)
- "Model comparison" (GPT-4 vs Claude Sonnet vs Gemini for same task)

### 6. Real-Time Guardrails

Use observability data to trigger **real-time circuit breakers**:

```python
# Pseudocode
if current_conversation_cost > 1.0:  # $1 threshold
    raise CostLimitExceeded("Conversation too expensive, aborting")

if hallucination_score > 0.8:  # Detected via output validation
    return fallback_response()
```

Grafana alerts can trigger webhooks to pause runaway agents.

---

## Conclusion

AI agents introduce unique observability challenges that traditional APM tools don't address. **OpenInference** extends OpenTelemetry with AI-specific semantic conventions, transforming the "black box" of generative AI into a transparent, cost-efficient, and secure production environment.

### The Four Pillars of AI Observability

Traditional observability has three pillars (Traces, Metrics, Logs). **AI systems require four**:

1. **Traces** - Hierarchical agent reasoning chains (AGENT → CHAIN → TOOL → LLM)
2. **Metrics** - Token usage, latency, cost attribution, request rates
3. **Logs** - Structured audit logs with user_id, trace_id, timestamps
4. **Evaluation** - Relevancy, faithfulness, correctness, hallucination detection

**Plus a critical fifth element**: **Human-in-the-Loop approval gates** for high-stakes actions, with observability proving enforcement.

**What complete AI observability enables**:

- **Hierarchical tracing** of agent reasoning chains with full context propagation
- **Token-based FinOps** tracking usage, cost per user/feature/conversation
- **Evaluation metrics** (automated and human) for quality assurance
- **HITL approval gates** with audit trails proving compliance
- **Distributed tracing** across multi-agent systems and microservices
- **Vendor-agnostic telemetry** (Grafana, Arize Phoenix, any OTLP backend)

**Key takeaways**:

1. **Initialize early** - Configure TracerProvider and MeterProvider BEFORE importing AI clients or creating agents
2. **Use StrandsInstrumentor** to wrap framework classes and emit OpenInference-compliant spans automatically
3. **Processor ordering matters** - Add OpenInference processor BEFORE OTLP exporter
4. **Add evaluation as a fourth pillar** - Automated (LLM-as-judge) + human spot checks
5. **Enforce HITL gates** - System prompt + tool-level enforcement + audit logging
6. **Export to Grafana LGTM stack** (Loki, Grafana, Tempo, Mimir) via OTLP for unified observability
7. **Use local collectors** (ADOT, Alloy) to redact PII and batch data before cloud export
8. **Implement tail sampling** to control costs while preserving error and slow traces
9. **Avoid cardinality explosion** - Never use unbounded values as metric labels
10. **Prove compliance** - Query traces to verify every high-stakes action had HITL approval

**Production-ready pattern (get-me-a-coke project)**:
- Strands Agents SDK with automatic OTel instrumentation
- OpenInference processor for AI semantic conventions
- **Evaluation**: Async LLM-as-judge attached to traces
- **HITL approval gates**: Two-step purchase flow with tool-level enforcement
- **Audit logging**: Every purchase logged with user_id, trace_id, timestamp
- Dual export: CloudWatch (AWS-native) + Grafana Cloud (AI dashboards)
- AWS AgentCore Runtime for managed agent hosting
- PII redaction at collector level
- Resource attributes for environment filtering
- **Compliance queries**: Prove every purchase had HITL approval via TraceQL

**The 2026 AI FinOps Era**: As we enter 2026, observability has become mission-critical for:
- **Cost control**: Track spend per user, feature, and conversation; identify expensive prompts
- **Quality assurance**: Monitor hallucination rates, tool-calling loops, and response relevancy via evaluation metrics
- **Safety enforcement**: Detect prompt injection, PII leakage, and toxic content through guardrails
- **Governance & compliance**: Prove HITL approval gates are enforced; audit high-stakes actions
- **Performance optimization**: Identify slow reasoning chains and inefficient prompts via token-to-task ratios

**The shift**: AI observability is no longer optional. Regulated industries (finance, healthcare) now **require** proof that:
1. Human approval was obtained for high-stakes actions
2. Every action is auditable (who, what, when, why)
3. Quality metrics meet SLA targets (hallucination rate < 2%)
4. PII is redacted before leaving the network

As AI agent architectures mature from simple chatbots to complex multi-agent systems with real-world consequences, observability has shifted from "nice to have" to **regulatory requirement** and **table stakes** for production deployments.

---

## References

### Primary Sources

This document integrates insights from **74 technical sources** on LLM and AI agent observability, covering:
- OpenInference standard and semantic conventions
- OpenTelemetry integration patterns
- Grafana LGTM stack (Loki, Grafana, Tempo, Mimir)
- AWS runtime deployment (Lambda, ECS, AgentCore)
- Strands Agents instrumentation
- AI FinOps strategies for 2026
- PII redaction and compliance patterns

**Source compilation**: [OpenInference and Strands Agents NotebookLM](https://notebooklm.google.com/notebook/ceb17812-0419-4b47-bc40-28c6e701dc43) (74 sources, May 2026)

### Key Technical Resources

- [OpenInference Specification](https://github.com/Arize-ai/openinference) - Vendor-agnostic AI observability standard
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/) - Standard telemetry attributes
- [OpenTelemetry GenAI Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) - Experimental AI semantic conventions
- [Grafana Tempo + TraceQL](https://grafana.com/docs/tempo/latest/traceql/) - Distributed tracing and query language
- [Grafana Alloy](https://grafana.com/docs/alloy/latest/) - OpenTelemetry collector distribution
- [AWS Distro for OpenTelemetry (ADOT)](https://aws-otel.github.io/) - AWS OTel distribution
- [Strands Agents SDK](https://github.com/strands-ai/strands-agents) - Python agent framework
- [OpenLIT SDK](https://github.com/openlit/openlit) - Turnkey LLM instrumentation
- [Arize Phoenix](https://docs.arize.com/phoenix) - AI observability platform (open-source)

### Project Implementation

- [Get Me a Coke Project](../README.md) - Production reference implementation
- [Technical Environment](../technical-environment.md) - Stack and deployment details
- [AgentCore Setup](./agentcore-setup.md) - AWS Bedrock AgentCore configuration

---

**Document Version**: 2.0  
**Last Updated**: 2026-05-26  
**Authors**: Claude Sonnet 4.5 (AI Engineering Team, DNX)  
**Research Sources**: 74 technical documents on AI observability, OpenInference, and Grafana integration

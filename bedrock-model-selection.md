# Bedrock Model Selection — ap-southeast-2 (Sydney)

**AWS Account**: <AWS_ACCOUNT_ID> (`nonprod-dnxai`)  
**Region**: ap-southeast-2  
**Date**: 2026-05-19

## Decision: Nemotron 3 Nano 30B A3B

Primary model for the agent's tool-calling and agentic reasoning.

**Model ID**: `nvidia.nemotron-nano-3-30b`  
**Inference type**: ON_DEMAND  
**Modalities**: Text → Text

### Why Nemotron over Qwen3 32B

Both are available on-demand in Sydney at similar parameter counts, but Nemotron wins on every axis that matters for this project:

| Criteria | Nemotron 3 Nano 30B | Qwen3 32B |
|----------|--------------------:|----------:|
| **Input cost (per 1M tokens)** | $0.0618 | $0.1545 |
| **Output cost (per 1M tokens)** | $0.2472 | $0.6180 |
| **Cost ratio** | 1x | 2.5x |
| **BFCL v4 (tool calling)** | 53.76 | 46.40 |
| **TauBench V2 (agentic)** | 49.04 | 47.70 |
| **IFBench (instruction following)** | 71.51 | 51.00 |
| **Active params per forward pass** | 3.2B | 32B |
| **Throughput vs Qwen3 MoE** | 3.3x faster | baseline |
| **Context window** | 1M tokens | 128K tokens |

### Architecture Highlights

- Hybrid Mamba-Transformer + Mixture-of-Experts (128 experts, 6 active)
- Only 3.2B parameters active per token (10% activation ratio)
- Trained with multi-step agentic tool use SFT + RL (Workplace Assistant, BFCL v4)
- XML-style tool calling tags (reduced escaping issues)
- Reasoning on/off toggle — use OFF for simple tool calls, ON for complex orchestration
- DPO-based tool hallucination reduction (near-zero hallucination rate)

### Reasoning Mode Guidance

| Scenario | Reasoning | Why |
|----------|-----------|-----|
| Simple tool call (list products, purchase) | OFF | Saves tokens, lower latency |
| Multi-step orchestration (retry logic, error handling) | ON | Better accuracy on complex flows |
| Budget-constrained batch operations | OFF | Minimize output tokens |

## Fallback / Escalation Model

**Claude Haiku 4.5** via `au.anthropic.claude-haiku-4-5-20251001-v1:0` inference profile.

- Input: ~$1.00/1M tokens, Output: ~$5.00/1M tokens
- Best-in-class tool_use reliability (Anthropic native format)
- Use when Nemotron fails on a complex multi-tool chain or when native Bedrock Converse API tool_use format is required

## Embedding Model (for future knowledge base)

**Amazon Titan Text Embeddings V2** (`amazon.titan-embed-text-v2:0`)
- On-demand in Sydney
- Good for RAG if we add product catalog search later

## Available Inference Profiles (for reference)

| Profile | Model | Routing |
|---------|-------|---------|
| `au.anthropic.claude-haiku-4-5-20251001-v1:0` | Claude Haiku 4.5 | Sydney + Melbourne |
| `au.anthropic.claude-sonnet-4-6` | Claude Sonnet 4.6 | Sydney + Melbourne |
| `au.anthropic.claude-opus-4-7` | Claude Opus 4.7 | Sydney + Melbourne |
| `apac.amazon.nova-micro-v1:0` | Nova Micro | APAC-wide |
| `apac.amazon.nova-lite-v1:0` | Nova Lite | APAC-wide |
| `apac.amazon.nova-pro-v1:0` | Nova Pro | APAC-wide |

## Cost Estimate (PoC usage)

Assuming ~1000 agent invocations/day, ~2K input + 1K output tokens per invocation:

| Model | Daily cost |
|-------|--------:|
| Nemotron 3 Nano 30B | ~$0.31 |
| Qwen3 32B | ~$0.77 |
| Claude Haiku 4.5 | ~$7.00 |

Nemotron keeps PoC costs negligible.

# Business Logic Model: AI Agent

## Overview

The agent is an autonomous buyer that receives natural language instructions, reasons about them, and executes purchases from the vending machine API. It uses Strands SDK's model-driven orchestration (plan → act → observe loop) with AgentCore Payments handling the x402 flow transparently.

## Core Business Flow

```
User Instruction (e.g., "Buy me a coke")
      |
      v
+--[Mode?]--+
|            |
Single-shot  REPL
|            |
v            v
Execute      Loop:
instruction    Prompt → Execute → Display
      |              |
      v              v
Agent Reasoning Loop (Strands SDK)
      |
      v
1. Discover products (GET /products)
2. Select appropriate product
3. Attempt purchase (POST /purchase/{id})
4. [402 received → AgentCore Payments auto-pays → retry]
5. Receive dispensed confirmation
      |
      v
Report result to user (minimal output)
```

## Business Processes

### 1. Single-Shot Execution
- **Input**: CLI argument string (e.g., `"Buy me a coke"`)
- **Process**: Create agent → invoke with instruction → print result → exit
- **Output**: Minimal confirmation or error message
- **Business Rule**: Process exits after single execution (exit code 0 on success, 1 on failure)

### 2. Interactive REPL
- **Input**: User types instructions in a loop
- **Process**: Create agent → loop (prompt → invoke → display) until exit
- **Output**: Agent responses (purchase results, conversation, errors)
- **Business Rules**:
  - Agent supports general conversation (not just purchases)
  - "exit", "quit", or Ctrl+C ends the session
  - Each turn is independent (no persistent memory across sessions)

### 3. Autonomous Purchase (Agent Reasoning)
- **Input**: Natural language purchase instruction
- **Process** (driven by Strands SDK model loop):
  1. Agent reasons about the instruction
  2. Calls `http_request` tool to GET /products from vending machine
  3. Parses catalog, selects product matching user intent
  4. Calls `http_request` tool to POST /purchase/{product_id}
  5. Receives 402 → AgentCore Payments plugin intercepts and pays automatically
  6. Request retried with payment proof → receives 200 (dispensed)
  7. Agent reports success to user
- **Output**: Minimal confirmation (e.g., "Purchased: Coke ✓")
- **Business Rules**:
  - Agent uses `http_request` from `strands_tools` for all HTTP calls
  - AgentCore Payments handles 402 transparently (no custom payment logic)
  - Agent selects product based on natural language matching

### 4. Error Handling
- **Input**: Various failure conditions
- **Process**: Agent detects error and reports clearly
- **Output**: Human-readable error message
- **Error Scenarios**:
  - Vending machine unreachable → "Vending machine unavailable at [URL]"
  - Product not found (404) → "Product not found. Available: coke, water, juice"
  - Payment failure → "Payment failed: [reason from AgentCore]"
  - Unknown instruction → Agent responds conversationally

## Agent Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Model | nvidia.nemotron-nano-3-30b | Hardcoded in agent.py |
| Tools | `http_request` (from strands_tools) | Agent definition |
| Plugins | AgentCorePaymentsPlugin | Agent definition |
| System Prompt | Defines agent role and behavior | `get_system_prompt()` |
| Vending Machine URL | From .env (`VENDING_MACHINE_URL`) | config.py |

## System Prompt Design

The system prompt instructs the agent to:
1. Act as a buyer that purchases items from vending machines
2. Use HTTP requests to discover and purchase products
3. Report results minimally (just the outcome)
4. Handle errors gracefully with clear messages
5. Support general conversation when not purchasing

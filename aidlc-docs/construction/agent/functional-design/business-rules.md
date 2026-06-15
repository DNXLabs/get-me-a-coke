# Business Rules: AI Agent

## Agent Behavior Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| AGT-001 | Agent MUST use `http_request` tool for all HTTP communication | Tools list in Agent definition |
| AGT-002 | Agent MUST NOT implement custom payment logic — AgentCore Payments handles 402 | Plugin configuration |
| AGT-003 | Agent MUST report results minimally (product name + success/failure indicator) | System prompt instruction |
| AGT-004 | Agent MUST handle errors gracefully with user-friendly messages | System prompt instruction |
| AGT-005 | Agent MUST support general conversation in REPL mode | System prompt instruction |
| AGT-006 | Agent uses nvidia.nemotron-nano-3-30b model via Bedrock | Model configuration |

## CLI Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| CLI-001 | Default mode is single-shot (positional argument) | argparse configuration |
| CLI-002 | `--interactive` flag enables REPL mode | argparse flag |
| CLI-003 | Single-shot exits with code 0 on success, 1 on failure | sys.exit() |
| CLI-004 | REPL exits on "exit", "quit", or Ctrl+C (KeyboardInterrupt) | Input loop logic |
| CLI-005 | REPL displays a prompt indicator (e.g., "> ") | Input prompt |

## Payment Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| PAY-001 | AgentCore Payments plugin auto-detects 402 responses | Plugin behavior (SDK) |
| PAY-002 | Payment uses testnet USDC on base-sepolia | Payment Manager configuration |
| PAY-003 | Spending limits enforced by AgentCore payment sessions | AgentCore configuration |
| PAY-004 | Payment Manager ARN loaded from .env configuration | config.py |

## Configuration Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| CFG-001 | All configuration loaded from .env file | python-dotenv / pydantic-settings |
| CFG-002 | Required config: VENDING_MACHINE_URL, AWS_PROFILE, AWS_REGION | Config validation |
| CFG-003 | Required for payments: PAYMENT_MANAGER_ARN, PAYMENT_INSTRUMENT_ID, USER_ID | Config validation |
| CFG-004 | Missing required config raises clear error at startup | Config class validation |

## Error Handling Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| ERR-001 | Connection errors → "Vending machine unavailable at [URL]" | Exception handling in agent or tool |
| ERR-002 | 404 responses → "Product not found" + list available products | Agent reasoning from response |
| ERR-003 | Payment failures → "Payment failed: [reason]" | AgentCore error propagation |
| ERR-004 | Unexpected errors → generic message, no stack trace to user | Top-level exception handler |

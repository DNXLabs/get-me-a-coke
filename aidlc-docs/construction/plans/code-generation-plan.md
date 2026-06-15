# Code Generation Plan: Get Me a Coke

## Project Context
- **Type**: Greenfield monorepo (monolith with `src/` packages)
- **Workspace Root**: `/Users/thiagosinjishimadaramos/dnx/Internal Practices/ai-dnx/projects/get-me-a-coke`
- **Application Code**: Workspace root (`src/`, `tests/`, `infra/`)
- **Documentation**: `aidlc-docs/` only

## Generation Sequence

Units are generated in dependency order:
1. **Project Setup** (shared config, pyproject.toml)
2. **Unit 1: Vending Machine API** (independent)
3. **Unit 3: Observability** (independent module)
4. **Unit 2: Agent** (depends on observability module)
5. **Unit 4: Infrastructure** (CDK, references units 1+2)

---

## Step 1: Project Setup
- [ ] Create `pyproject.toml` with all dependencies and tool configuration
- [ ] Create `src/vending_machine/__init__.py`
- [ ] Create `src/agent/__init__.py`
- [ ] Create `src/observability/__init__.py`
- [ ] Create `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [ ] Update `.env.example` with all required environment variables
- [ ] Create `src/config.py` (shared configuration loading from .env)

**Stories**: Foundation for all stories

---

## Step 2: Vending Machine — Models
- [ ] Create `src/vending_machine/models.py` (Product, PaymentTerms, PurchaseResponse, ErrorResponse)

**Stories**: 1.1, 1.2, 1.3, 1.4

---

## Step 3: Vending Machine — x402 Payment Logic
- [ ] Create `src/vending_machine/x402.py` (get_payment_terms, validate_payment)

**Stories**: 1.2, 1.3

---

## Step 4: Vending Machine — Routes
- [ ] Create `src/vending_machine/routes.py` (list_products, purchase, health_check)

**Stories**: 1.1, 1.2, 1.3, 1.4

---

## Step 5: Vending Machine — App Factory + Handler
- [ ] Create `src/vending_machine/app.py` (create_app, FastAPI configuration)
- [ ] Create `src/vending_machine/handler.py` (Mangum Lambda entry point)

**Stories**: 1.1, 1.2, 1.3, 1.4, 4.2

---

## Step 6: Vending Machine — Unit Tests
- [ ] Create `tests/unit/test_vending_machine/__init__.py`
- [ ] Create `tests/unit/test_vending_machine/test_models.py`
- [ ] Create `tests/unit/test_vending_machine/test_x402.py`
- [ ] Create `tests/unit/test_vending_machine/test_routes.py`

**Stories**: 1.1, 1.2, 1.3, 1.4

---

## Step 7: Observability — Telemetry Module
- [ ] Create `src/observability/telemetry.py` (configure_telemetry, provider setup with StrandsAgentsToOpenInferenceProcessor)
- [ ] Create `src/observability/exporters.py` (OTLP exporter configuration)

**Stories**: 3.1, 3.2, 3.3

---

## Step 8: Observability — Unit Tests
- [ ] Create `tests/unit/test_observability/__init__.py`
- [ ] Create `tests/unit/test_observability/test_telemetry.py`

**Stories**: 3.1, 3.2, 3.3

---

## Step 9: Agent — Configuration
- [ ] Create `src/agent/config.py` (AgentConfig with pydantic-settings, loads from .env)

**Stories**: 2.1, 2.2

---

## Step 10: Agent — Agent Definition
- [ ] Create `src/agent/agent.py` (create_agent, get_system_prompt, AgentCore Payments plugin setup)

**Stories**: 2.3, 2.4, 2.5, 2.6

---

## Step 11: Agent — CLI Entry Point
- [ ] Create `src/agent/cli.py` (main, run_single_shot, run_interactive with argparse)

**Stories**: 2.1, 2.2

---

## Step 12: Agent — Unit Tests
- [ ] Create `tests/unit/test_agent/__init__.py`
- [ ] Create `tests/unit/test_agent/test_config.py`
- [ ] Create `tests/unit/test_agent/test_agent.py` (mocked Bedrock + mocked HTTP)
- [ ] Create `tests/unit/test_agent/test_cli.py`

**Stories**: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6

---

## Step 13: Integration Tests
- [ ] Create `tests/integration/test_agent_vending_machine.py` (agent calls local vending machine with mocked payments, real Bedrock)
- [ ] Create `tests/integration/conftest.py` (fixtures: local vending machine server, mocked AgentCore)

**Stories**: 2.3, 2.4 (cross-unit)

---

## Step 14: Infrastructure — CDK Setup
- [ ] Create `infra/app.py` (CDK app entry point)
- [ ] Create `infra/stacks/__init__.py`
- [ ] Create `infra/stacks/vending_machine_stack.py` (Lambda + API Gateway)
- [ ] Create `infra/stacks/agent_stack.py` (IAM role for AgentCore)
- [ ] Create `infra/cdk.json`
- [ ] Create `infra/requirements.txt`

**Stories**: 4.2, 4.3

---

## Step 15: Documentation + Deployment Artifacts
- [ ] Create `README.md` (project overview, setup instructions, local dev, deployment)
- [ ] Create `docs/agentcore-setup.md` (manual AgentCore Payments prerequisites)
- [ ] Create `Makefile` (common commands: dev, test, lint, deploy)

**Stories**: 4.1, 4.2, 4.3

---

## Step 16: Code Generation Summary
- [ ] Create `aidlc-docs/construction/vending-machine/code/code-summary.md`
- [ ] Create `aidlc-docs/construction/agent/code/code-summary.md`
- [ ] Create `aidlc-docs/construction/observability/code/code-summary.md`
- [ ] Create `aidlc-docs/construction/infrastructure/code/code-summary.md`

---

## Total: 16 Steps

**Files to generate**: ~35 files
**Coverage**: All 16 user stories mapped to generation steps

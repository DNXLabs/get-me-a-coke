# Build and Test Summary

## Quick Reference

| Command | Purpose |
|---------|---------|
| `make install` | Install all dependencies |
| `make test` | Run unit tests |
| `make test-integration` | Run integration tests |
| `make lint` | Run ruff linter |
| `make format` | Auto-format code |
| `make type-check` | Run mypy strict |
| `make dev` | Start vending machine locally |
| `make agent` | Start agent interactive mode |
| `make agent-buy` | Single-shot: buy a coke |
| `make synth` | Validate CDK templates |
| `make deploy` | Deploy all stacks |
| `make destroy` | Tear down all resources |

## Test Pyramid

```
         /\
        /  \     Integration (real Bedrock, mocked payments)
       /    \    2 tests + 1 commented (expensive)
      /------\
     /        \   Unit Tests (all mocked)
    /          \  ~20 tests across 6 files
   /____________\
```

## Quality Gates

| Gate | Command | Expected |
|------|---------|----------|
| Unit tests pass | `make test` | All green |
| Linter clean | `make lint` | No errors |
| Types valid | `make type-check` | No errors |
| CDK synthesizes | `make synth` | No errors |
| Integration tests | `make test-integration` | All green |

## Deployment Checklist

1. ✅ All unit tests pass
2. ✅ Linter and type checker clean
3. ✅ CDK synth succeeds
4. ✅ Integration tests pass (optional — requires AWS)
5. Deploy: `make deploy`
6. Configure AgentCore: see `docs/agentcore-setup.md`
7. Test deployed agent: update `VENDING_MACHINE_URL` in .env to API Gateway URL

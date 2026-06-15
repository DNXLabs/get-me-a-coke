# Get Me a Coke — Deploy Status

**Account**: <AWS_ACCOUNT_ID> (nonprod-dnxai)
**Region**: ap-southeast-2
**Profile**: `nonprod-dnxai`
**Last checked**: 2026-05-26T17:21 AEST

## Stacks

| Stack | Resources | Status | Outputs |
|-------|-----------|--------|---------|
| `GetMeACoke-VendingMachine-dev` | Lambda + HTTP API Gateway | ✅ Deployed | https://wmor87hzr8.execute-api.ap-southeast-2.amazonaws.com/ |
| `GetMeACoke-WalletService-dev` | Lambda + HTTP API Gateway | ✅ Deployed | https://6ekyw5dph7.execute-api.ap-southeast-2.amazonaws.com/ |
| `GetMeACoke-Agent-dev` | IAM role (AgentCore) | ✅ Deployed | arn:aws:iam::<AWS_ACCOUNT_ID>:role/get-me-a-coke-agentcore-runtime-dev |
| `GetMeACoke-Approval-dev` | Step Functions + Activity + IAM Policy | ✅ Deployed | arn:aws:states:ap-southeast-2:<AWS_ACCOUNT_ID>:stateMachine:get-me-a-coke-purchase-approval-dev |

## Endpoint Tests

| Endpoint | Result |
|----------|--------|
| `GET /health` (vending machine) | ✅ `{"status": "healthy"}` |
| `GET /products` | ✅ 3 products (coke, water, juice) |
| `POST /purchase/coke` | ✅ HTTP 402 with payment terms |
| `GET /health` (wallet) | ✅ `{"status": "healthy"}` |
| `GET /balance` (with API key) | ✅ 1.0000 USDC |

## HITL Approval Flow

```
Agent calls execute_purchase
  → Starts Step Functions execution
  → Polls Activity for task token
  → CLI prompts: "Approve? [y/N]"
  → y: SendTaskSuccess → purchase proceeds
  → n: SendTaskFailure → purchase rejected
```

## Commands

```bash
make deploy    # Deploy all stacks
make destroy   # Tear down all stacks
make synth     # Validate CDK templates
make agent     # Run agent (interactive, HITL enabled)
```

## Cleanup

To destroy all resources:
```bash
make destroy
```

This removes:
- 2 Lambda functions + 2 API Gateway HTTP APIs
- 1 IAM role + policy (AgentCore)
- 1 Step Functions state machine + Activity + IAM policy (Approval)
- Associated CloudWatch log groups

## Notes

- Agent runs locally (`make agent`) — not deployed as a cloud service
- Wallet is mock (in-memory, resets on cold start)
- Bedrock model: nvidia.nemotron-nano-3-30b (available in ap-southeast-2)
- Observability: OTel/OpenInference → Grafana Cloud + Sigil AI observability
- HITL: Step Functions Activity pattern — hard gate, model cannot bypass

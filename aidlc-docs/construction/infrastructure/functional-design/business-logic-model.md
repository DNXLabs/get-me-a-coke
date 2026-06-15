# Business Logic Model: Infrastructure (CDK)

## Overview

The infrastructure unit defines AWS resources as CDK (Python) stacks. It follows the pattern established by the existing `DNXFoundation-*` stacks but creates new project-specific stacks. Does NOT modify existing deployments.

## Stacks

### Stack 1: GetMeACoke-VendingMachine-dev

| Resource | Type | Purpose |
|----------|------|---------|
| Lambda Function | AWS::Lambda::Function | Runs FastAPI app via Mangum |
| API Gateway HTTP API | AWS::ApiGatewayV2::Api | Public HTTP endpoint for vending machine |
| API Gateway Integration | AWS::ApiGatewayV2::Integration | Routes all requests to Lambda |
| Lambda Permission | AWS::Lambda::Permission | Allows API Gateway to invoke Lambda |

**Lambda Configuration:**
- Runtime: Python 3.12
- Handler: `vending_machine.handler.handler`
- Memory: 256 MB (sufficient for FastAPI)
- Timeout: 30 seconds
- Architecture: arm64 (Graviton, cheaper)
- Code: Packaged from `src/vending_machine/`

**API Gateway Configuration:**
- Protocol: HTTP (not REST — simpler, cheaper)
- Stage: `$default` (auto-deploy)
- Route: `$default` → Lambda integration (catch-all)
- CORS: Enabled (allow all origins for PoC)

### Stack 2: GetMeACoke-Agent-dev

| Resource | Type | Purpose |
|----------|------|---------|
| IAM Role | AWS::IAM::Role | AgentCore Runtime execution role |
| IAM Policy | AWS::IAM::Policy | Bedrock invoke (Nemotron Nano) + observability |

**IAM Role Configuration:**
- Trust: `bedrock-agentcore.amazonaws.com` (same pattern as foundation)
- Permissions:
  - `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `bedrock:Converse`, `bedrock:ConverseStream` on `arn:aws:bedrock:*::foundation-model/nvidia.nemotron-nano-3-30b`
  - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` (CloudWatch)
  - `xray:PutTraceSegments`, `xray:PutTelemetryRecords` (X-Ray/ADOT)
  - `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage` (container pull)

**Note**: AgentCore Runtime itself is configured via `agentcore` CLI (not CDK) — CDK only provisions the IAM role and any supporting resources.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate stacks per component | Independent lifecycle, can deploy/destroy individually |
| New IAM role (not reusing foundation) | Foundation role only allows Claude Sonnet 4; we need Nemotron Nano |
| Follow foundation naming pattern | Consistency with existing `DNXFoundation-*` stacks |
| arm64 Lambda | Cost optimization (Graviton is ~20% cheaper) |
| HTTP API (not REST API) | Simpler, cheaper, sufficient for PoC |
| No VPC | PoC doesn't need private networking |

## Deployment Order

1. `GetMeACoke-VendingMachine-dev` — deploys Lambda + API Gateway
2. `GetMeACoke-Agent-dev` — deploys IAM role for AgentCore
3. AgentCore Runtime configured via CLI (uses the IAM role from step 2)

## Stack Outputs

### GetMeACoke-VendingMachine-dev
| Output | Value | Used By |
|--------|-------|---------|
| `VendingMachineUrl` | API Gateway endpoint URL | Agent configuration (.env) |
| `LambdaFunctionArn` | Lambda ARN | Reference only |

### GetMeACoke-Agent-dev
| Output | Value | Used By |
|--------|-------|---------|
| `AgentRuntimeRoleArn` | IAM role ARN | AgentCore CLI configuration |

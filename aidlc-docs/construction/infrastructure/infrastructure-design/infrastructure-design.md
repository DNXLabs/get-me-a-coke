# Infrastructure Design: Get Me a Coke

## Overview

All infrastructure defined as AWS CDK (Python). Two stacks deployed to `ap-southeast-2` using profile `nonprod-dnxai`. Follows the pattern established by existing `DNXFoundation-*` stacks.

## Architecture Diagram

```
+--------------------------------------------------+
|  AWS Account: <AWS_ACCOUNT_ID> (nonprod-dnxai)       |
|  Region: ap-southeast-2                          |
|                                                  |
|  +--------------------------------------------+ |
|  | Stack: GetMeACoke-VendingMachine-dev        | |
|  |                                            | |
|  |  +------------------+    +---------------+ | |
|  |  | API Gateway      |    | Lambda        | | |
|  |  | (HTTP API)       |--->| (Python 3.12) | | |
|  |  | $default stage   |    | arm64         | | |
|  |  +------------------+    | 256MB / 30s   | | |
|  |                          +---------------+ | |
|  +--------------------------------------------+ |
|                                                  |
|  +--------------------------------------------+ |
|  | Stack: GetMeACoke-Agent-dev                 | |
|  |                                            | |
|  |  +------------------+                      | |
|  |  | IAM Role         |                      | |
|  |  | (AgentCore       |                      | |
|  |  |  Runtime exec)   |                      | |
|  |  +------------------+                      | |
|  +--------------------------------------------+ |
|                                                  |
|  +--------------------------------------------+ |
|  | AgentCore Runtime (managed, not in CDK)     | |
|  |                                            | |
|  |  Agent container → uses IAM role above     | |
|  |  Configured via: agentcore CLI             | |
|  +--------------------------------------------+ |
|                                                  |
|  External:                                       |
|  +------------------+                            |
|  | Grafana Cloud    | <-- OTLP from agent        |
|  | (Tempo/Mimir/    |                            |
|  |  Loki)           |                            |
|  +------------------+                            |
+--------------------------------------------------+
```

## Stack 1: GetMeACoke-VendingMachine-dev

### Resources

| Resource | CDK Construct | Configuration |
|----------|--------------|---------------|
| Lambda Function | `aws_lambda.Function` | Python 3.12, arm64, 256MB, 30s timeout |
| API Gateway HTTP API | `aws_apigatewayv2.HttpApi` | Default stage, CORS enabled |
| Lambda Integration | `HttpLambdaIntegration` | Proxy all requests to Lambda |
| Default Route | `HttpRoute` | `$default` → Lambda integration |

### Lambda Configuration

```python
# CDK construct parameters
function = aws_lambda.Function(
    self, "VendingMachineFunction",
    function_name="get-me-a-coke-vending-machine-dev",
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    architecture=aws_lambda.Architecture.ARM_64,
    handler="vending_machine.handler.handler",
    code=aws_lambda.Code.from_asset("../src", exclude=["agent/**", "observability/**"]),
    memory_size=256,
    timeout=Duration.seconds(30),
    environment={
        "POWERTOOLS_SERVICE_NAME": "vending-machine",
    },
)
```

### API Gateway Configuration

```python
api = aws_apigatewayv2.HttpApi(
    self, "VendingMachineApi",
    api_name="get-me-a-coke-vending-machine-dev",
    cors_preflight=aws_apigatewayv2.CorsPreflightOptions(
        allow_origins=["*"],
        allow_methods=[aws_apigatewayv2.CorsHttpMethod.ANY],
        allow_headers=["*"],
    ),
)
```

### Stack Outputs

| Output Key | Value | Purpose |
|-----------|-------|---------|
| `VendingMachineUrl` | API Gateway endpoint URL | Agent configuration |
| `LambdaFunctionName` | Function name | Debugging/logs |

---

## Stack 2: GetMeACoke-Agent-dev

### Resources

| Resource | CDK Construct | Configuration |
|----------|--------------|---------------|
| IAM Role | `aws_iam.Role` | Trusted by bedrock-agentcore.amazonaws.com |
| IAM Policy | Inline policy | Bedrock invoke + observability + ECR |

### IAM Role Configuration

```python
role = aws_iam.Role(
    self, "AgentRuntimeRole",
    role_name="get-me-a-coke-agentcore-runtime-dev",
    assumed_by=aws_iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
    description="Execution role for Get Me a Coke agent on AgentCore Runtime",
)
```

### IAM Policy Statements

| Sid | Actions | Resources |
|-----|---------|-----------|
| `BedrockInvokeNemotron` | bedrock:InvokeModel, InvokeModelWithResponseStream, Converse, ConverseStream | `arn:aws:bedrock:*::foundation-model/nvidia.nemotron-nano-3-30b` |
| `ObservabilityLogsAndTraces` | logs:CreateLogGroup, CreateLogStream, PutLogEvents, xray:PutTraceSegments, PutTelemetryRecords, cloudwatch:PutMetricData | `*` |
| `EcrPullForAgentImage` | ecr:GetAuthorizationToken, BatchCheckLayerAvailability, GetDownloadUrlForLayer, BatchGetImage | `*` |
| `MarketplaceAutoSubscribe` | aws-marketplace:Subscribe, Unsubscribe, ViewSubscriptions | `*` |

### Stack Outputs

| Output Key | Value | Purpose |
|-----------|-------|---------|
| `AgentRuntimeRoleArn` | IAM role ARN | AgentCore CLI configuration |

---

## AgentCore Runtime (Not in CDK)

AgentCore Runtime is configured via the `agentcore` CLI, not CDK. The workflow:

1. CDK deploys the IAM role (`GetMeACoke-Agent-dev` stack)
2. Developer configures AgentCore Runtime:
   ```bash
   agentcore configure \
     --agent-name get-me-a-coke-agent-dev \
     --role-arn <from CDK output> \
     --region ap-southeast-2
   ```
3. Developer launches the agent:
   ```bash
   agentcore launch
   ```

---

## Deployment Commands

```bash
# From infra/ directory
cd infra

# Synthesize (validate templates)
cdk synth

# Deploy all stacks
cdk deploy --all --profile nonprod-dnxai

# Deploy individual stack
cdk deploy GetMeACoke-VendingMachine-dev --profile nonprod-dnxai
cdk deploy GetMeACoke-Agent-dev --profile nonprod-dnxai

# Destroy all
cdk destroy --all --profile nonprod-dnxai
```

## CDK Project Structure

```
infra/
├── app.py                          # CDK app entry point
├── stacks/
│   ├── __init__.py
│   ├── vending_machine_stack.py    # Lambda + API Gateway
│   └── agent_stack.py             # IAM role for AgentCore
├── cdk.json                        # CDK configuration
├── requirements.txt                # aws-cdk-lib, constructs
└── tests/
    └── test_stacks.py             # Snapshot tests (optional)
```

## Environment Configuration

### cdk.json
```json
{
  "app": "python app.py",
  "context": {
    "env": "dev",
    "project": "get-me-a-coke",
    "region": "ap-southeast-2",
    "account": "<AWS_ACCOUNT_ID>"
  }
}
```

## Networking

- **No VPC** — PoC doesn't need private networking
- **Public API Gateway** — accessible from anywhere (PoC)
- **Lambda in default VPC** — no custom networking
- **TLS** — provided by API Gateway by default (HTTPS endpoint)

## Cost Estimate (PoC)

| Resource | Estimated Cost |
|----------|---------------|
| Lambda (minimal usage) | ~$0/month (free tier) |
| API Gateway (minimal usage) | ~$0/month (free tier) |
| AgentCore Runtime | Pay-per-invocation |
| Bedrock (Nemotron Nano) | Pay-per-token |
| **Total** | Negligible for PoC usage |

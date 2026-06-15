"""CDK Stack: Agent — IAM role for AgentCore Runtime."""

from __future__ import annotations

from aws_cdk import (
    CfnOutput,
    Stack,
    aws_iam as iam,
)
from constructs import Construct


class AgentStack(Stack):
    """Deploy IAM role for the Get Me a Coke agent on AgentCore Runtime."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(scope, construct_id, **kwargs)

        # IAM Role for AgentCore Runtime
        role = iam.Role(
            self,
            "AgentRuntimeRole",
            role_name="get-me-a-coke-agentcore-runtime-dev",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Execution role for Get Me a Coke agent on AgentCore Runtime",
        )

        # Bedrock model invocation — Nemotron Nano
        role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockInvokeNemotron",
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:Converse",
                    "bedrock:ConverseStream",
                ],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/nvidia.nemotron-nano-3-30b",
                ],
            )
        )

        # Observability — CloudWatch + X-Ray (required by AgentCore ADOT)
        role.add_to_policy(
            iam.PolicyStatement(
                sid="ObservabilityLogsAndTraces",
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "cloudwatch:PutMetricData",
                ],
                resources=["*"],
            )
        )

        # ECR pull for agent container image
        role.add_to_policy(
            iam.PolicyStatement(
                sid="EcrPullForAgentImage",
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=["*"],
            )
        )

        # Marketplace auto-subscribe (required for some Bedrock models)
        role.add_to_policy(
            iam.PolicyStatement(
                sid="MarketplaceAutoSubscribe",
                actions=[
                    "aws-marketplace:Subscribe",
                    "aws-marketplace:Unsubscribe",
                    "aws-marketplace:ViewSubscriptions",
                ],
                resources=["*"],
            )
        )

        # Output
        CfnOutput(self, "AgentRuntimeRoleArn", value=role.role_arn)

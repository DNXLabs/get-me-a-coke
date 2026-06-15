"""CDK Stack: Vending Machine API — Lambda + API Gateway HTTP API."""

from __future__ import annotations

from aws_cdk import (
    BundlingOptions,
    CfnOutput,
    Duration,
    Stack,
    aws_lambda as lambda_,
)
from aws_cdk.aws_apigatewayv2 import CorsHttpMethod, CorsPreflightOptions, HttpApi
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct


class VendingMachineStack(Stack):
    """Deploy the Vending Machine API as Lambda behind API Gateway HTTP API."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(scope, construct_id, **kwargs)

        # Lambda function with bundled dependencies
        function = lambda_.Function(
            self,
            "VendingMachineFunction",
            function_name="get-me-a-coke-vending-machine-dev",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.ARM_64,
            handler="vending_machine.handler.handler",
            code=lambda_.Code.from_asset(
                "../src",
                exclude=["agent/**", "**/__pycache__/**", "wallet_service/**"],
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install fastapi mangum pydantic pydantic-settings"
                        " opentelemetry-sdk opentelemetry-exporter-otlp"
                        " opentelemetry-instrumentation-fastapi"
                        " -t /asset-output"
                        " && cp -r . /asset-output/",
                    ],
                ),
            ),
            memory_size=256,
            timeout=Duration.seconds(30),
            environment={
                "POWERTOOLS_SERVICE_NAME": "vending-machine",
            },
        )

        # API Gateway HTTP API
        api = HttpApi(
            self,
            "VendingMachineApi",
            api_name="get-me-a-coke-vending-machine-dev",
            cors_preflight=CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[CorsHttpMethod.ANY],
                allow_headers=["*"],
            ),
            default_integration=HttpLambdaIntegration(
                "LambdaIntegration",
                handler=function,
            ),
        )

        # Outputs
        CfnOutput(self, "VendingMachineUrl", value=api.url or "")
        CfnOutput(self, "LambdaFunctionName", value=function.function_name)

"""CDK Stack: Purchase Approval — Step Functions HITL gate using Activity callback."""

from __future__ import annotations

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_iam as iam,
    aws_stepfunctions as sfn,
)
from constructs import Construct


class ApprovalStack(Stack):
    """Step Functions state machine with Activity-based HITL approval gate.

    Flow:
    1. Agent starts execution with purchase details
    2. State machine reaches Activity task and waits
    3. CLI polls GetActivityTask, receives token + purchase details
    4. CLI prompts user for approval
    5. CLI sends SendTaskSuccess (approved) or SendTaskFailure (rejected)
    6. State machine completes with approved/rejected status
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(scope, construct_id, **kwargs)

        # Activity — external worker (CLI) polls this for approval tasks
        activity = sfn.Activity(
            self,
            "PurchaseApprovalActivity",
            activity_name="get-me-a-coke-purchase-approval-dev",
        )

        # State machine definition
        wait_for_approval = sfn.CustomState(
            self,
            "WaitForApproval",
            state_json={
                "Type": "Task",
                "Resource": activity.activity_arn,
                "TimeoutSeconds": 300,
                "ResultPath": "$.approval",
            },
        )

        approved = sfn.Pass(self, "Approved", result=sfn.Result.from_object({"status": "approved"}))
        rejected = sfn.Pass(self, "Rejected", result=sfn.Result.from_object({"status": "rejected"}))

        wait_for_approval.add_catch(rejected, errors=["States.Timeout", "States.TaskFailed"])
        wait_for_approval.next(approved)

        state_machine = sfn.StateMachine(
            self,
            "PurchaseApprovalStateMachine",
            state_machine_name="get-me-a-coke-purchase-approval-dev",
            definition_body=sfn.DefinitionBody.from_chainable(wait_for_approval),
            timeout=Duration.minutes(10),
        )

        # IAM policy for the agent/CLI to interact with the approval workflow
        agent_policy = iam.ManagedPolicy(
            self,
            "AgentApprovalPolicy",
            managed_policy_name="get-me-a-coke-approval-agent-dev",
            statements=[
                iam.PolicyStatement(
                    sid="StartApprovalExecution",
                    actions=["states:StartExecution"],
                    resources=[state_machine.state_machine_arn],
                ),
                iam.PolicyStatement(
                    sid="GetActivityTask",
                    actions=["states:GetActivityTask"],
                    resources=[activity.activity_arn],
                ),
                iam.PolicyStatement(
                    sid="SendTaskCallbacks",
                    actions=["states:SendTaskSuccess", "states:SendTaskFailure"],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="DescribeExecution",
                    actions=["states:DescribeExecution"],
                    resources=[f"{state_machine.state_machine_arn}*"],
                ),
            ],
        )

        # Outputs
        CfnOutput(self, "StateMachineArn", value=state_machine.state_machine_arn)
        CfnOutput(self, "ActivityArn", value=activity.activity_arn)
        CfnOutput(self, "AgentApprovalPolicyArn", value=agent_policy.managed_policy_arn)

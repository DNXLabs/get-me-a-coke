"""CDK app entry point for Get Me a Coke infrastructure."""

from __future__ import annotations

import os

import aws_cdk as cdk

from stacks.agent_stack import AgentStack
from stacks.approval_stack import ApprovalStack
from stacks.vending_machine_stack import VendingMachineStack
from stacks.wallet_service_stack import WalletServiceStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT") or app.node.try_get_context("account"),
    region=os.environ.get("CDK_DEFAULT_REGION") or app.node.try_get_context("region") or "ap-southeast-2",
)

VendingMachineStack(app, "GetMeACoke-VendingMachine-dev", env=env)
WalletServiceStack(app, "GetMeACoke-WalletService-dev", env=env)
AgentStack(app, "GetMeACoke-Agent-dev", env=env)
ApprovalStack(app, "GetMeACoke-Approval-dev", env=env)

app.synth()

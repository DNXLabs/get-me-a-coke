"""Purchase approval tool — starts Step Functions execution for HITL gate.

Instead of executing the purchase directly, this tool:
1. Starts a Step Functions execution with the purchase details
2. Polls the Activity for the task token
3. Prompts the user for approval (via CLI input)
4. Sends SendTaskSuccess or SendTaskFailure
5. If approved, executes the actual purchase
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime

import boto3
import httpx
from strands import tool

from observability.sigil_tools import sigil_tool_wrapper

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("audit.purchase")


def _sfn_client():  # type: ignore[no-untyped-def]
    return boto3.client("stepfunctions", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))


def _state_machine_arn() -> str:
    return os.environ.get(
        "APPROVAL_STATE_MACHINE_ARN",
        "arn:aws:states:ap-southeast-2:000000000000:stateMachine:get-me-a-coke-purchase-approval-dev",
    )


def _activity_arn() -> str:
    return os.environ.get(
        "APPROVAL_ACTIVITY_ARN",
        "arn:aws:states:ap-southeast-2:000000000000:activity:get-me-a-coke-purchase-approval-dev",
    )


def _wallet_url() -> str:
    return os.environ.get("WALLET_SERVICE_URL", "http://localhost:8001")


def _wallet_headers() -> dict[str, str]:
    return {"X-API-Key": os.environ.get("WALLET_API_KEY", "dev-wallet-key-change-me")}


def _vending_machine_url() -> str:
    return os.environ.get("VENDING_MACHINE_URL", "http://localhost:8000")


def _user_id() -> str:
    return os.environ.get("PAYMENT_USER_ID", "unknown")


@tool
@sigil_tool_wrapper
def execute_purchase(product_id: str) -> dict:
    """Buy a product. Triggers a human approval gate before completing.

    Args:
        product_id: The product to buy (must match a pending quote)
    """
    from agent.tools.vending_machine import _pending_quote

    # Gate: enforce quote exists
    if _pending_quote is None:
        return {"success": False, "error": "No pending quote. Call get_purchase_quote first."}

    if _pending_quote["product_id"] != product_id:
        return {
            "success": False,
            "error": f"Quote is for '{_pending_quote['product_id']}', not '{product_id}'.",
        }

    quote = _pending_quote
    user_id = _user_id()

    # Start Step Functions execution
    sfn = _sfn_client()
    execution_input = {
        "product_id": quote["product_id"],
        "price": quote["price"],
        "currency": quote["currency"],
        "network": quote["network"],
        "wallet_address": quote["wallet_address"],
        "user_id": user_id,
        "quoted_at": quote["quoted_at"],
    }

    try:
        exec_resp = sfn.start_execution(
            stateMachineArn=_state_machine_arn(),
            input=json.dumps(execution_input),
        )
        execution_arn = exec_resp["executionArn"]
        logger.info("Approval workflow started: %s", execution_arn)
    except Exception as e:
        return {"success": False, "error": f"Failed to start approval workflow: {e}"}

    # Poll Activity for task token (blocks until state machine reaches the activity)
    try:
        task_resp = sfn.get_activity_task(
            activityArn=_activity_arn(),
            workerName="cli-agent",
        )
    except Exception as e:
        return {"success": False, "error": f"Failed to get approval task: {e}"}

    task_token = task_resp.get("taskToken")
    if not task_token:
        return {"success": False, "error": "No approval task received (timeout or error)."}

    # Prompt user for approval
    print(f"\n{'='*50}")
    print(f"🔒 PURCHASE APPROVAL REQUIRED")
    print(f"{'='*50}")
    print(f"  Product:  {quote['product_id']}")
    print(f"  Price:    {quote['price']} {quote['currency']}")
    print(f"  Network:  {quote['network']}")
    print(f"  User:     {user_id}")
    print(f"{'='*50}")

    try:
        response = input("  Approve? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        response = "n"

    if response in ("y", "yes"):
        # Approved — send success callback
        sfn.send_task_success(taskToken=task_token, output=json.dumps({"approved": True}))
        logger.info("Purchase approved by user")

        # Execute the actual purchase
        return _do_purchase(quote, user_id)
    else:
        # Rejected — send failure callback
        sfn.send_task_failure(
            taskToken=task_token,
            error="UserRejected",
            cause="User declined the purchase",
        )
        audit_logger.info(json.dumps({
            "event": "purchase_rejected",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "product_id": quote["product_id"],
            "price": quote["price"],
        }))
        return {"success": False, "status": "rejected", "message": "Purchase declined by user."}


def _do_purchase(quote: dict, user_id: str) -> dict:
    """Execute the actual purchase after approval."""
    import agent.tools.vending_machine as vm

    audit_entry = {
        "event": "purchase_approved",
        "timestamp": datetime.now(UTC).isoformat(),
        "user_id": user_id,
        "product_id": quote["product_id"],
        "price": quote["price"],
        "currency": quote["currency"],
        "network": quote["network"],
        "recipient": quote["wallet_address"],
        "quoted_at": quote["quoted_at"],
    }
    audit_logger.info(json.dumps(audit_entry))

    try:
        # Pay via Wallet Service
        pay_resp = httpx.post(
            f"{_wallet_url()}/pay",
            headers=_wallet_headers(),
            json={
                "amount": quote["price"],
                "recipient_address": quote["wallet_address"],
                "network": quote["network"],
            },
            timeout=10,
        )
        pay_resp.raise_for_status()
        pay_result = pay_resp.json()

        if not pay_result.get("success"):
            vm._pending_quote = None
            return {"success": False, "error": f"Payment failed: {pay_result.get('error')}"}

        payment_proof = pay_result["payment_proof"]

        # Dispense product
        response = httpx.post(
            f"{_vending_machine_url()}/purchase/{quote['product_id']}",
            headers={"X-PAYMENT": payment_proof},
            timeout=10,
        )

        vm._pending_quote = None

        if response.status_code == 200:
            result = response.json()
            audit_logger.info(json.dumps({
                **audit_entry,
                "event": "purchase_completed",
                "transaction_hash": payment_proof,
            }))
            return {
                "success": True,
                "product_id": result.get("product_id", quote["product_id"]),
                "product_name": result.get("product_name", quote["product_id"]),
                "amount_paid": quote["price"],
                "currency": quote["currency"],
                "approved_by": user_id,
                "approval_method": "step_functions_hitl",
            }

        return {"success": False, "error": f"Dispense failed: {response.status_code}"}

    except httpx.ConnectError as e:
        vm._pending_quote = None
        return {"success": False, "error": f"Service unavailable: {e}"}

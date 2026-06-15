"""Vending machine tools — two-step purchase with auditable approval gate.

Flow:
1. get_purchase_quote(product_id) → returns terms, stores pending quote
2. User approves in conversation
3. execute_purchase(product_id) → pays + dispenses, logs audit trail
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime

import httpx
from strands import tool

from observability.sigil_tools import sigil_tool_wrapper

logger = logging.getLogger(__name__)

# Audit logger — separate from app logs, structured JSON for CloudWatch/SIEM
audit_logger = logging.getLogger("audit.purchase")

# Pending quote state (per-session)
_pending_quote: dict | None = None


def _get_vending_machine_url() -> str:
    return os.environ.get("VENDING_MACHINE_URL", "http://localhost:8000")


def _wallet_url() -> str:
    return os.environ.get("WALLET_SERVICE_URL", "http://localhost:8001")


def _wallet_headers() -> dict[str, str]:
    return {"X-API-Key": os.environ.get("WALLET_API_KEY", "dev-wallet-key-change-me")}


def _user_id() -> str:
    return os.environ.get("PAYMENT_USER_ID", "unknown")


@tool
@sigil_tool_wrapper
def list_products() -> dict:
    """List all products available in the vending machine."""
    url = _get_vending_machine_url()
    try:
        response = httpx.get(f"{url}/products", timeout=10)
        response.raise_for_status()
        return {"products": response.json()}
    except httpx.ConnectError:
        return {"error": f"Vending machine unavailable at {url}"}
    except Exception as e:
        return {"error": str(e)}


@tool
@sigil_tool_wrapper
def get_purchase_quote(product_id: str) -> dict:
    """Get the price and payment terms for a product.

    Args:
        product_id: The product to quote (e.g., "coke", "water", "juice")
    """
    global _pending_quote  # noqa: PLW0603
    url = _get_vending_machine_url()

    try:
        response = httpx.post(f"{url}/purchase/{product_id}", timeout=10)

        if response.status_code == 404:
            return {"success": False, "error": f"Product '{product_id}' not found."}

        if response.status_code != 402:
            return {"success": False, "error": f"Unexpected response: {response.status_code}"}

        terms = response.json()
        _pending_quote = {
            "product_id": product_id,
            "price": terms.get("price", "0"),
            "currency": terms.get("currency", "USDC"),
            "wallet_address": terms.get("wallet_address", ""),
            "network": terms.get("network", "base-sepolia"),
            "quoted_at": datetime.now(UTC).isoformat(),
        }

        return {
            "success": True,
            "quote": {
                "product_id": product_id,
                "price": _pending_quote["price"],
                "currency": _pending_quote["currency"],
                "network": _pending_quote["network"],
            },
            "message": "Quote ready. Ask the user to approve before calling execute_purchase.",
        }

    except httpx.ConnectError:
        return {"success": False, "error": f"Vending machine unavailable at {url}"}


@tool
def execute_purchase(product_id: str) -> dict:
    """Execute a previously quoted purchase. Only call AFTER user approves the quote.

    This is an audited action — it logs who approved, what was purchased, and when.

    Args:
        product_id: The product to buy (must match a pending quote)

    Returns:
        Purchase result or error if no valid quote exists.
    """
    global _pending_quote  # noqa: PLW0603

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
    url = _get_vending_machine_url()

    # Audit: log approval
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
            fail = {**audit_entry, "event": "purchase_failed", "reason": pay_result.get("error")}
            audit_logger.info(json.dumps(fail))
            _pending_quote = None
            return {"success": False, "error": f"Payment failed: {pay_result.get('error')}"}

        payment_proof = pay_result["payment_proof"]

        # Retry with payment proof
        response = httpx.post(
            f"{url}/purchase/{product_id}",
            headers={"X-PAYMENT": payment_proof},
            timeout=10,
        )

        _pending_quote = None

        if response.status_code == 200:
            result = response.json()
            audit_logger.info(json.dumps({
                **audit_entry,
                "event": "purchase_completed",
                "transaction_hash": payment_proof,
                "product_name": result.get("product_name"),
            }))
            return {
                "success": True,
                "product_id": result.get("product_id", product_id),
                "product_name": result.get("product_name", product_id),
                "amount_paid": quote["price"],
                "currency": quote["currency"],
                "approved_by": user_id,
            }

        audit_logger.info(json.dumps({
            **audit_entry, "event": "purchase_failed", "reason": f"dispense:{response.status_code}",
        }))
        return {"success": False, "error": f"Dispense failed: {response.status_code}"}

    except httpx.ConnectError as e:
        _pending_quote = None
        return {"success": False, "error": f"Service unavailable: {e}"}
    except httpx.HTTPStatusError as e:
        _pending_quote = None
        return {"success": False, "error": f"Wallet auth failed: {e.response.status_code}"}

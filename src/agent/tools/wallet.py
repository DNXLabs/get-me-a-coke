"""Wallet tools — HTTP clients calling the Wallet Service.

The agent uses these tools to check balance and make payments.
All actual wallet logic lives in the Wallet Service.
"""

from __future__ import annotations

import logging
import os

import httpx
from strands import tool

from observability.sigil_tools import sigil_tool_wrapper

logger = logging.getLogger(__name__)


def _wallet_url() -> str:
    return os.environ.get("WALLET_SERVICE_URL", "http://localhost:8001")


def _wallet_headers() -> dict[str, str]:
    return {"X-API-Key": os.environ.get("WALLET_API_KEY", "dev-wallet-key-change-me")}


@tool
@sigil_tool_wrapper
def wallet_get_balance() -> dict:
    """Check the current USDC wallet balance."""
    try:
        resp = httpx.get(f"{_wallet_url()}/balance", headers=_wallet_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        return {"error": f"Wallet service unavailable at {_wallet_url()}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"Wallet auth failed: {e.response.status_code}"}


@tool
@sigil_tool_wrapper
def wallet_pay(amount: str, recipient_address: str, network: str = "base-sepolia") -> dict:
    """Send a USDC payment to a recipient address.

    Args:
        amount: Amount in USDC (e.g., "0.01")
        recipient_address: Wallet address to pay
        network: Blockchain network (default: base-sepolia)
    """
    try:
        resp = httpx.post(
            f"{_wallet_url()}/pay",
            headers=_wallet_headers(),
            json={"amount": amount, "recipient_address": recipient_address, "network": network},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        return {"success": False, "error": f"Wallet service unavailable at {_wallet_url()}"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Wallet auth failed: {e.response.status_code}"}

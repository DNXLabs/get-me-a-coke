"""Wallet Service — FastAPI app with API key authentication.

A shared payment service that any authorized agent can call to check balance and make payments.
In production this would wrap real wallet infrastructure (Coinbase CDP, etc.).
For the POC it simulates a USDC wallet on Base Sepolia.
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# --- Auth ---

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")
VALID_API_KEY = os.environ.get("WALLET_API_KEY", "dev-wallet-key-change-me")


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


# --- Models ---


class PayRequest(BaseModel):
    amount: str
    recipient_address: str
    network: str = "base-sepolia"


class PayResponse(BaseModel):
    success: bool
    transaction_hash: str | None = None
    payment_proof: str | None = None
    amount_paid: str | None = None
    currency: str = "USDC"
    network: str = "base-sepolia"
    remaining_balance: str | None = None
    error: str | None = None


class BalanceResponse(BaseModel):
    address: str
    balance_usdc: str
    network: str
    currency: str = "USDC"


# --- Wallet State (in-memory mock) ---

_wallet_state = {
    "address": "0xMockAgentWallet1234567890abcdef1234567890",
    "balance_usdc": 1.00,
    "network": "base-sepolia",
    "transactions": [],
}

# --- App ---

app = FastAPI(
    title="Wallet Service",
    description="Shared payment service with API key auth. Simulates USDC wallet for POC.",
    version="0.1.0",
)

# Instrument for distributed tracing (propagates trace context from agent)
from observability.fastapi_telemetry import instrument_fastapi_app

instrument_fastapi_app(app, service_name="wallet-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/balance", response_model=BalanceResponse)
async def get_balance(_: str = Depends(verify_api_key)) -> BalanceResponse:
    """Return current wallet balance. Requires API key."""
    return BalanceResponse(
        address=_wallet_state["address"],
        balance_usdc=f"{_wallet_state['balance_usdc']:.4f}",
        network=_wallet_state["network"],
    )


@app.post("/pay", response_model=PayResponse)
async def pay(req: PayRequest, _: str = Depends(verify_api_key)) -> PayResponse:
    """Execute a USDC payment. Requires API key."""
    pay_amount = float(req.amount)

    if pay_amount <= 0:
        return PayResponse(success=False, error="Payment amount must be positive")

    if pay_amount > _wallet_state["balance_usdc"]:
        bal = _wallet_state["balance_usdc"]
        return PayResponse(
            success=False,
            error=f"Insufficient funds. Balance: {bal:.4f} USDC, required: {pay_amount:.4f} USDC",
        )

    _wallet_state["balance_usdc"] -= pay_amount
    tx_hash = f"0xmock_tx_{len(_wallet_state['transactions']) + 1:04d}_{req.recipient_address[:8]}"
    _wallet_state["transactions"].append({
        "hash": tx_hash,
        "amount": req.amount,
        "recipient": req.recipient_address,
        "network": req.network,
    })

    return PayResponse(
        success=True,
        transaction_hash=tx_hash,
        payment_proof=tx_hash,
        amount_paid=req.amount,
        network=req.network,
        remaining_balance=f"{_wallet_state['balance_usdc']:.4f}",
    )

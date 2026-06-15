"""AWS Lambda entry point for Wallet Service."""

from __future__ import annotations

from mangum import Mangum

from wallet_service.app import app

handler = Mangum(app, lifespan="off")

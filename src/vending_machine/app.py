"""FastAPI application factory for the Vending Machine API."""

from __future__ import annotations

from fastapi import FastAPI

from vending_machine.routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Get Me a Coke — Vending Machine",
        description="x402-compatible vending machine API that accepts agent payments",
        version="0.1.0",
    )
    app.include_router(router)

    from observability.fastapi_telemetry import instrument_fastapi_app

    instrument_fastapi_app(app, service_name="vending-machine")

    return app


app = create_app()

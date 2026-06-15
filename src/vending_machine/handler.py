"""AWS Lambda entry point using Mangum."""

from __future__ import annotations

from mangum import Mangum

from vending_machine.app import app

handler = Mangum(app, lifespan="off")

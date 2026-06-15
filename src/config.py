"""Shared configuration loading from .env file."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Application-wide configuration loaded from environment / .env file."""

    # AWS
    aws_profile: str = "nonprod-dnxai"
    aws_region: str = "ap-southeast-2"

    # Vending Machine
    vending_machine_url: str = "http://localhost:8000"

    # Bedrock Model
    bedrock_model_id: str = "nvidia.nemotron-nano-3-30b"

    # AgentCore Payments
    payment_manager_arn: str = ""
    payment_instrument_id: str = ""
    payment_session_id: str = ""
    payment_user_id: str = "thiago"

    # Grafana Observability
    grafana_otlp_endpoint: str = ""
    grafana_instance_id: str = ""
    grafana_api_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def load_config() -> AppConfig:
    """Load configuration from .env file and environment variables."""
    return AppConfig()

"""Agent configuration loaded from .env file."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings


class AgentConfig(BaseSettings):
    """Configuration for the AI agent."""

    # AWS
    aws_profile: str = "nonprod-dnxai"
    aws_region: str = "ap-southeast-2"

    # Vending Machine target
    vending_machine_url: str = "http://localhost:8000"

    # Wallet Service
    wallet_service_url: str = "http://localhost:8001"
    wallet_api_key: str = "dev-wallet-key-change-me"

    # Bedrock Model
    bedrock_model_id: str = "nvidia.nemotron-nano-3-30b"

    # Bedrock Prompt Management
    bedrock_prompt_id: str = ""
    bedrock_prompt_version: str = "DRAFT"

    # AgentCore Payments
    payment_manager_arn: str = ""
    payment_instrument_id: str = ""
    payment_session_id: str = ""
    payment_user_id: str = "thiago"

    # Observability
    grafana_otlp_endpoint: str = ""
    grafana_instance_id: str = ""
    grafana_api_token: str = ""

    # Sigil
    sigil_endpoint: str = ""
    sigil_protocol: Literal["http", "grpc", "none"] = "http"
    sigil_auth_mode: Literal["basic", "bearer", "tenant"] = "basic"
    sigil_auth_tenant_id: str = ""
    sigil_auth_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def payments_configured(self) -> bool:
        """Check if AgentCore Payments credentials are configured."""
        return bool(self.payment_manager_arn and self.payment_instrument_id)

    @property
    def observability_configured(self) -> bool:
        """Check if Grafana observability credentials are configured."""
        return bool(self.grafana_otlp_endpoint and self.grafana_instance_id and self.grafana_api_token)

    @property
    def sigil_configured(self) -> bool:
        """True when all required Sigil credentials are present."""
        return bool(
            self.sigil_endpoint.strip()
            and self.sigil_auth_tenant_id.strip()
            and self.sigil_auth_token.strip()
        )

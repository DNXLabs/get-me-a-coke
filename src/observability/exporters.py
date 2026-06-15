"""OTLP exporter configuration for Grafana Cloud."""

from __future__ import annotations

import base64


def build_grafana_auth_headers(instance_id: str, api_token: str) -> dict[str, str]:
    """Build Basic auth headers for Grafana Cloud OTLP endpoint.

    Grafana Cloud expects: Authorization: Basic base64(instance_id:api_token)
    """
    credentials = f"{instance_id}:{api_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def build_otlp_endpoint(grafana_otlp_endpoint: str, signal: str) -> str:
    """Build the full OTLP endpoint URL for a specific signal.

    Args:
        grafana_otlp_endpoint: Base Grafana OTLP endpoint (e.g., https://stack.grafana.net/otlp)
        signal: One of 'traces', 'metrics', 'logs'

    Returns:
        Full endpoint URL (e.g., https://stack.grafana.net/otlp/v1/traces)
    """
    base = grafana_otlp_endpoint.rstrip("/")
    return f"{base}/v1/{signal}"

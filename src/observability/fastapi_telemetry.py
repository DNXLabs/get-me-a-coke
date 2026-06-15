"""FastAPI service telemetry — OTel instrumentation for HTTP services (wallet, vending machine).

Provides distributed tracing: propagates trace context from agent → service,
emits server spans for each request, and exports to the same Grafana backend.
"""

from __future__ import annotations

import base64
import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def instrument_fastapi_app(app: object, service_name: str) -> None:
    """Instrument a FastAPI app with OpenTelemetry tracing.

    Reads configuration from environment variables (same as the agent):
    - Standard: OTEL_EXPORTER_OTLP_ENDPOINT + OTEL_EXPORTER_OTLP_HEADERS
    - Grafana: GRAFANA_OTLP_ENDPOINT + GRAFANA_INSTANCE_ID + GRAFANA_API_TOKEN

    If neither is configured, sets up a TracerProvider without export so trace
    context propagation still works (spans are generated but not exported).
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:
        logger.warning(
            "opentelemetry-instrumentation-fastapi not installed. "
            "Service telemetry disabled for %s.",
            service_name,
        )
        return

    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    otel_headers = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
    grafana_endpoint = os.environ.get("GRAFANA_OTLP_ENDPOINT", "")
    grafana_instance_id = os.environ.get("GRAFANA_INSTANCE_ID", "")
    grafana_api_token = os.environ.get("GRAFANA_API_TOKEN", "")

    has_otel_env = bool(otel_endpoint and otel_headers)
    has_grafana = bool(grafana_endpoint and grafana_instance_id and grafana_api_token)

    resource = Resource.create({
        "service.name": service_name,
        "service.version": "0.1.0",
        "deployment.environment": os.environ.get("DEPLOYMENT_ENV", "dev"),
    })

    provider = TracerProvider(resource=resource)

    if has_otel_env:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    elif has_grafana:
        credentials = f"{grafana_instance_id}:{grafana_api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers = {"Authorization": f"Basic {encoded}"}
        endpoint = f"{grafana_endpoint.rstrip('/')}/v1/traces"
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers))
        )
    else:
        logger.info(
            "No OTLP export configured for %s. Trace context propagation active but spans not exported.",
            service_name,
        )

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI instrumentation active: service=%s", service_name)

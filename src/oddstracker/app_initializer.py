import logging
import os

from opentelemetry import trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger(__name__)


OTLP_EXPORTER_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")


def setup_tracing() -> None:
    # insecure = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "false").lower() == "true"

    if OTLP_EXPORTER_ENDPOINT:
        logger.info(
            f"Setting up OpenTelemetry tracing with endpoint: {OTLP_EXPORTER_ENDPOINT}"
        )
    else:
        logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT not set. Tracing is disabled.")
        return

    exporter = OTLPSpanExporter(endpoint=OTLP_EXPORTER_ENDPOINT)

    provider = TracerProvider(
        resource=Resource.create(
            {
                "SERVICE_NAME": "rotoreader",
                "SERVICE_NAMESPACE": "sportsstack",
            }
        )
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    set_global_textmap(
        CompositePropagator(
            [
                TraceContextTextMapPropagator(),
                W3CBaggagePropagator(),
            ]
        )
    )

    logger.info(
        f"Initialized OpenTelemetry tracing to endpoint: {OTLP_EXPORTER_ENDPOINT}"
    )


def instrument_tracing(app) -> None:
    if OTLP_EXPORTER_ENDPOINT:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation for OpenTelemetry tracing configured.")


def instrument_prometheus(app) -> None:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app)
    logging.info("Prometheus metrics instrumentation configured.")

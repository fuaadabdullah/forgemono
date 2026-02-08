from fastapi import FastAPI
from pydantic import BaseModel

# Initialize OpenTelemetry tracing
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.distro import distro

    # Initialize distro
    distro.configure()

    # Create resource
    resource = Resource.create(
        {
            "service.name": "gaslight-backend",
            "service.version": "1.0.0",
        }
    )

    # Configure tracing
    trace.set_tracer_provider(TracerProvider(resource=resource))

    # Add OTLP trace exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4318",
        insecure=True,
    )
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    print("✅ OpenTelemetry initialized for gaslight-backend")

except Exception as e:
    print(f"⚠️  OpenTelemetry not available: {e}")

app = FastAPI()

# Instrument FastAPI app
try:
    FastAPIInstrumentor().instrument_app(app)
    print("✅ FastAPI instrumentation enabled")
except Exception as e:
    print(f"⚠️  FastAPI instrumentation failed: {e}")


class RouteRequest(BaseModel):
    npc_id: str
    mission: int
    message: str


class RouteResponse(BaseModel):
    npc_response: str
    goblin_hint: str
    mission_status: str
    next_step: int


@app.post("/route", response_model=RouteResponse)
def route_message(req: RouteRequest):
    """A minimal route that returns placeholder NPC and goblin replies.

    Replace this with the backend routing logic tied to mission and NPC.
    """
    return RouteResponse(
        npc_response=f"NPC({req.npc_id}) responds to: {req.message}",
        goblin_hint="Goblin side-comment...",
        mission_status="in_progress",
        next_step=req.mission + 1,
    )

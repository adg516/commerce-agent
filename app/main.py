from pathlib import Path
import re
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent import CommerceAgent
from app.catalog import get_catalog_registry
from app.csv_parser import parse_catalog_csv
from app.models import ChatRequest, ChatResponse
from app.tools import CatalogTools


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Commerce Agent", version="0.1.0")
# SCALE: add middleware for structured request logging (correlation IDs, latency,
# user agent) and integrate with an observability stack (OpenTelemetry, Jaeger).
# SCALE: add rate limiting middleware (slowapi or API gateway level) to protect
# against abuse and control per-user request budgets.
agent = CommerceAgent()
catalog_registry = get_catalog_registry()
tools = CatalogTools()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    # SCALE: add deep health checks — verify DB connectivity, Redis ping,
    # OpenAI API reachability, and vector DB status. Return degraded status
    # if any dependency is unhealthy so k8s readiness probes can react.
    return {"status": "ok"}


@app.get("/api/products/{product_id}")
def get_product(product_id: str, catalog: str = "all") -> dict:
    product = catalog_registry.get_product(product_id, catalog_slug=catalog)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.model_dump()


@app.get("/api/catalogs")
def list_catalogs() -> dict:
    return tools.list_catalogs()


def _slugify_catalog_name(value: str) -> str:
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    cleaned = re.sub(r"[^a-z0-9]+", "-", spaced.lower()).strip("-")
    return cleaned or f"upload-{uuid4().hex[:8]}"


@app.post("/api/catalogs/upload")
async def upload_catalog(
    file: UploadFile = File(...),
    name: str = Form(""),
) -> dict:
    # SCALE: stream the uploaded file to object storage (S3/GCS) instead of
    # reading it all into memory. For large CSVs, process rows in batches.
    # SCALE: emit a pub/sub event (e.g. "catalog.uploaded") so downstream
    # services (search indexer, analytics) can react asynchronously.
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")

    try:
        csv_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = raw.decode("utf-8-sig", errors="ignore")

    slug_base = _slugify_catalog_name(name or Path(file.filename).stem)
    slug = f"upload-{slug_base}-{uuid4().hex[:6]}"
    products = parse_catalog_csv(csv_text, slug_prefix=slug.replace("-", "_"))
    if not products:
        raise HTTPException(status_code=400, detail="No rows could be parsed from the CSV.")

    upload_result = tools.register_uploaded_catalog(slug=slug, products=products)
    return {
        "catalog": {"slug": upload_result["slug"], "name": catalog_registry._display_name(slug)},
        "count": upload_result["count"],
        "catalogs": tools.list_catalogs()["catalogs"],
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # SCALE: make this endpoint async and offload the agent.chat() call to a
    # background task via pub/sub (Redis Streams, Kafka, SQS). Return a job ID
    # and let the frontend poll GET /api/chat/{job_id} or subscribe via WebSocket.
    # This prevents long-running LLM calls from blocking the ASGI worker pool.
    # SCALE: add per-user authentication (JWT/OAuth) and tie conversation_id
    # to the authenticated user for multi-tenant isolation.
    result = agent.chat(
        message=request.message,
        image_b64=request.image_b64,
        conversation_id=request.conversation_id,
        catalog_slug=request.catalog,
    )
    return ChatResponse(
        reply=result.reply,
        conversation_id=result.conversation_id,
        products=result.products,
        sources=result.sources,
        metadata=result.metadata,
    )

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent import CommerceAgent
from app.catalog import get_catalog_store
from app.models import ChatRequest, ChatResponse


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Commerce Agent", version="0.1.0")
agent = CommerceAgent()
catalog = get_catalog_store()

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
    return {"status": "ok"}


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.model_dump()


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = agent.chat(
        message=request.message,
        image_b64=request.image_b64,
        conversation_id=request.conversation_id,
    )
    return ChatResponse(
        reply=result.reply,
        conversation_id=result.conversation_id,
        products=result.products,
        sources=result.sources,
        metadata=result.metadata,
    )

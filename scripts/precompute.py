from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.catalog import build_embedding_text  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.models import Product  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to precompute embeddings.")

    raw_products = json.loads(settings.resolved_catalog_path.read_text(encoding="utf-8"))
    products = [Product.model_validate(item) for item in raw_products]
    client = OpenAI(api_key=settings.openai_api_key)

    embedding_inputs = [build_embedding_text(product) for product in products]
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=embedding_inputs,
    )

    embeddings = np.asarray([item.embedding for item in response.data], dtype=float)
    settings.resolved_embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(settings.resolved_embeddings_path, embeddings)

    print(f"Wrote {len(embeddings)} embeddings to {settings.resolved_embeddings_path}")


if __name__ == "__main__":
    main()

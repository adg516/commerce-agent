from __future__ import annotations

import argparse
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


def embed_catalog(client: OpenAI, model: str, catalog_path: Path, embeddings_path: Path) -> int:
    raw_products = json.loads(catalog_path.read_text(encoding="utf-8"))
    products = [Product.model_validate(item) for item in raw_products]
    embedding_inputs = [build_embedding_text(product) for product in products]
    response = client.embeddings.create(
        model=model,
        input=embedding_inputs,
    )

    embeddings = np.asarray([item.embedding for item in response.data], dtype=float)
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_path, embeddings)
    return len(embeddings)


def main() -> None:
    parser = argparse.ArgumentParser(description="Precompute embeddings for one or more catalogs.")
    parser.add_argument("--catalog", default="all", help="Catalog slug under data/catalogs (or 'all').")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to precompute embeddings.")

    client = OpenAI(api_key=settings.openai_api_key)
    root = settings.resolved_catalogs_root

    if args.catalog == "all":
        catalog_dirs = [
            path
            for path in sorted(root.iterdir())
            if path.is_dir() and not path.name.startswith("_") and (path / "catalog.json").exists()
        ]
    else:
        selected = root / args.catalog
        if not selected.exists():
            raise RuntimeError(f"Catalog '{args.catalog}' not found under {root}")
        catalog_dirs = [selected]

    for catalog_dir in catalog_dirs:
        catalog_path = catalog_dir / "catalog.json"
        embeddings_path = catalog_dir / "embeddings.npy"
        count = embed_catalog(
            client=client,
            model=settings.openai_embedding_model,
            catalog_path=catalog_path,
            embeddings_path=embeddings_path,
        )
        print(f"Wrote {count} embeddings to {embeddings_path}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from app.config import get_settings
from app.models import Product


def build_embedding_text(product: Product) -> str:
    """Build a rich text representation for semantic search."""
    return (
        f"{product.name}. {product.description}. "
        f"Category: {product.category}. Subcategory: {product.subcategory}. "
        f"Activity: {', '.join(product.activity)}. "
        f"Material: {product.material}. Fit: {product.fit}. "
        f"Color: {product.color}. Season: {', '.join(product.season)}. "
        f"Tags: {', '.join(product.tags)}."
    )


class CatalogStore:
    def __init__(self, catalog_slug: str, catalog_path: Path, embeddings_path: Path):
        self.catalog_slug = catalog_slug
        self.catalog_path = catalog_path
        self.embeddings_path = embeddings_path
        self.products = self._load_products()
        self.product_map = {product.id: product for product in self.products}
        self.product_index = {product.id: idx for idx, product in enumerate(self.products)}
        self.embedding_texts = [build_embedding_text(product) for product in self.products]
        self.embeddings = self._load_embeddings()

    def _load_products(self) -> list[Product]:
        raw_products = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        return [Product.model_validate(item) for item in raw_products]

    def _load_embeddings(self) -> np.ndarray | None:
        if not self.embeddings_path.exists():
            return None

        embeddings = np.load(self.embeddings_path)
        if len(embeddings) != len(self.products):
            raise ValueError("Embedding count does not match product count.")

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms

    def get_product(self, product_id: str) -> Product | None:
        return self.product_map.get(product_id)

    def get_reviews(self, product_id: str) -> list[dict[str, Any]]:
        product = self.get_product(product_id)
        if not product:
            return []

        average_rating = round(sum(review.rating for review in product.reviews) / len(product.reviews), 2)
        return [
            {
                "average_rating": average_rating,
                "snippet": review.text,
                "rating": review.rating,
            }
            for review in product.reviews
        ]

    def search(
        self,
        query_embedding: np.ndarray | None,
        query_text: str,
        filters: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        candidates = self._filter_products(filters)
        if not candidates:
            return []

        if self.embeddings is not None and query_embedding is not None:
            return self._vector_search(query_embedding=query_embedding, products=candidates, top_k=top_k)

        return self._keyword_fallback(query_text=query_text, products=candidates, top_k=top_k)

    def _filter_products(self, filters: dict[str, Any]) -> list[Product]:
        matched: list[Product] = []

        for product in self.products:
            if filters.get("category") and product.category != filters["category"]:
                continue
            if filters.get("subcategory") and product.subcategory != filters["subcategory"]:
                continue
            if filters.get("gender"):
                requested_gender = str(filters["gender"]).lower()
                product_gender = product.gender.lower()
                if requested_gender == "unisex":
                    if product_gender != "unisex":
                        continue
                elif product_gender not in (requested_gender, "unisex"):
                    continue
            if filters.get("activity") and filters["activity"] not in product.activity:
                continue
            if filters.get("color") and filters["color"].lower() not in product.color.lower():
                continue
            if filters.get("season") and filters["season"] not in product.season:
                continue
            if filters.get("max_price") is not None and product.price > float(filters["max_price"]):
                continue
            if filters.get("min_price") is not None and product.price < float(filters["min_price"]):
                continue
            matched.append(product)

        return matched

    def _vector_search(
        self,
        query_embedding: np.ndarray,
        products: list[Product],
        top_k: int,
    ) -> list[dict[str, Any]]:
        query_embedding = np.asarray(query_embedding, dtype=float)
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return self._keyword_fallback(query_text="", products=products, top_k=top_k)
        query_embedding = query_embedding / query_norm

        product_indices = [self.product_index[product.id] for product in products]
        candidate_matrix = self.embeddings[product_indices]
        scores = candidate_matrix @ query_embedding
        ranked_positions = np.argsort(scores)[::-1][:top_k]

        results: list[dict[str, Any]] = []
        for position in ranked_positions:
            product = products[int(position)]
            results.append(
                {
                    "product": product.model_dump(),
                    "score": round(float(scores[int(position)]), 4),
                    "match_reason": "semantic_similarity",
                    "catalog_slug": self.catalog_slug,
                }
            )
        return results

    def _keyword_fallback(
        self,
        query_text: str,
        products: list[Product],
        top_k: int,
    ) -> list[dict[str, Any]]:
        query_terms = {term for term in query_text.lower().replace(",", " ").split() if term}
        scored: list[tuple[float, Product]] = []

        for product in products:
            haystack = build_embedding_text(product).lower()
            score = sum(1 for term in query_terms if term in haystack)
            scored.append((float(score), product))

        ranked = sorted(scored, key=lambda item: (item[0], -item[1].price), reverse=True)[:top_k]
        return [
            {
                "product": product.model_dump(),
                "score": round(score, 4),
                "match_reason": "keyword_fallback",
                "catalog_slug": self.catalog_slug,
            }
            for score, product in ranked
        ]


class CatalogRegistry:
    def __init__(self, catalogs_root: Path, default_catalog_slug: str = "athletic"):
        self.catalogs_root = catalogs_root
        self.default_catalog_slug = default_catalog_slug
        self._stores: dict[str, CatalogStore] = {}
        self.reload()

    def reload(self) -> None:
        self._stores.clear()
        if not self.catalogs_root.exists():
            self.catalogs_root.mkdir(parents=True, exist_ok=True)

        for path in sorted(self.catalogs_root.iterdir()):
            if not path.is_dir():
                continue
            if path.name.startswith("_"):
                continue
            catalog_path = path / "catalog.json"
            embeddings_path = path / "embeddings.npy"
            if not catalog_path.exists():
                continue
            self._stores[path.name] = CatalogStore(
                catalog_slug=path.name,
                catalog_path=catalog_path,
                embeddings_path=embeddings_path,
            )

    def list_catalogs(self) -> list[dict[str, str]]:
        catalogs = []
        for slug in sorted(self._stores):
            catalogs.append(
                {
                    "slug": slug,
                    "name": slug.replace("-", " ").replace("_", " ").title(),
                }
            )
        return catalogs

    def get_store(self, catalog_slug: str | None) -> CatalogStore | None:
        slug = catalog_slug or self.default_catalog_slug
        return self._stores.get(slug)

    def search(
        self,
        *,
        catalog_slug: str | None,
        query_embedding: np.ndarray | None,
        query_text: str,
        filters: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        if catalog_slug and catalog_slug != "all":
            store = self.get_store(catalog_slug)
            if not store:
                return []
            return store.search(
                query_embedding=query_embedding,
                query_text=query_text,
                filters=filters,
                top_k=top_k,
            )

        merged_results: list[dict[str, Any]] = []
        for store in self._stores.values():
            merged_results.extend(
                store.search(
                    query_embedding=query_embedding,
                    query_text=query_text,
                    filters=filters,
                    top_k=top_k,
                )
            )

        merged_results.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
        return merged_results[:top_k]

    def get_product(self, product_id: str, catalog_slug: str | None = None) -> Product | None:
        if catalog_slug and catalog_slug != "all":
            store = self.get_store(catalog_slug)
            return store.get_product(product_id) if store else None

        for store in self._stores.values():
            product = store.get_product(product_id)
            if product:
                return product
        return None

    def get_reviews(self, product_id: str, catalog_slug: str | None = None) -> list[dict[str, Any]]:
        if catalog_slug and catalog_slug != "all":
            store = self.get_store(catalog_slug)
            return store.get_reviews(product_id) if store else []

        for store in self._stores.values():
            product = store.get_product(product_id)
            if product:
                return store.get_reviews(product_id)
        return []

    def save_uploaded_catalog(self, slug: str, products: list[dict[str, Any]]) -> tuple[Path, Path]:
        target_dir = self.catalogs_root / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        catalog_path = target_dir / "catalog.json"
        embeddings_path = target_dir / "embeddings.npy"
        catalog_path.write_text(json.dumps(products, indent=2), encoding="utf-8")
        return catalog_path, embeddings_path

    def register_uploaded_catalog(self, slug: str, catalog_path: Path, embeddings_path: Path) -> None:
        self._stores[slug] = CatalogStore(
            catalog_slug=slug,
            catalog_path=catalog_path,
            embeddings_path=embeddings_path,
        )


@lru_cache(maxsize=1)
def get_catalog_registry() -> CatalogRegistry:
    settings = get_settings()
    return CatalogRegistry(
        catalogs_root=settings.resolved_catalogs_root,
        default_catalog_slug=settings.default_catalog_slug,
    )

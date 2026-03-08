from __future__ import annotations

import re
from typing import Any

import numpy as np
from openai import OpenAI

from app.catalog import get_catalog_store
from app.config import Settings, get_settings


class CatalogTools:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.catalog = get_catalog_store()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def search_catalog_text(self, query: str, filters: dict[str, Any] | None = None, top_k: int = 5) -> dict[str, Any]:
        inferred_filters = self.infer_filters_from_text(query)
        merged_filters = dict(inferred_filters)
        if filters:
            merged_filters.update(filters)
        embedding = self._embed_text(query)
        matches = self.catalog.search(
            query_embedding=embedding,
            query_text=query,
            filters=merged_filters,
            top_k=top_k,
        )
        # If the LLM supplied overly strict filters that produce no candidates,
        # relax in stages: inferred query filters first, then fully unfiltered.
        if not matches and filters and inferred_filters != merged_filters:
            matches = self.catalog.search(
                query_embedding=embedding,
                query_text=query,
                filters=inferred_filters,
                top_k=top_k,
            )
        if not matches and (merged_filters or inferred_filters):
            matches = self.catalog.search(
                query_embedding=embedding,
                query_text=query,
                filters={},
                top_k=top_k,
            )
        return {
            "query": query,
            "filters": merged_filters,
            "matches": matches,
        }

    def search_catalog_image(
        self,
        image_description: str,
        filters: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        # A local CLIP/open_clip model could replace this text bridge by embedding
        # the raw image directly, but for this Pi-friendly take-home we keep the
        # runtime lightweight and reuse text embeddings instead.
        merged_filters = self._infer_image_filters(image_description)
        if filters:
            merged_filters.update(filters)
        embedding = self._embed_text(image_description)
        matches = self.catalog.search(
            query_embedding=embedding,
            query_text=image_description,
            filters=merged_filters,
            top_k=top_k,
        )
        return {
            "image_description": image_description,
            "filters": merged_filters,
            "matches": matches,
        }

    def get_product(self, product_id: str) -> dict[str, Any]:
        product = self.catalog.get_product(product_id)
        if not product:
            return {"error": f"Unknown product_id: {product_id}"}
        return {"product": product.model_dump()}

    def get_reviews(self, product_id: str) -> dict[str, Any]:
        product = self.catalog.get_product(product_id)
        if not product:
            return {"error": f"Unknown product_id: {product_id}"}
        return {"product_id": product_id, "reviews": self.catalog.get_reviews(product_id)}

    def describe_image(self, image_b64: str, user_prompt: str = "") -> str:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is required for image search.")

        prompt = (
            "Describe the product or outfit in this image for retail search. "
            "Focus on product category, color, material, fit, style, and use case. "
            "Reply with one concise paragraph only."
        )
        if user_prompt.strip():
            prompt += f" User context: {user_prompt.strip()}"

        response = self.client.chat.completions.create(
            model=self.settings.openai_vision_model,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content or "Unspecified athletic product."

    def _embed_text(self, text: str) -> np.ndarray | None:
        if not self.client:
            return None

        response = self.client.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=text,
        )
        return np.asarray(response.data[0].embedding, dtype=float)

    def infer_filters_from_text(self, text: str) -> dict[str, Any]:
        lowered = text.lower()
        filters: dict[str, Any] = {}

        price_patterns = [
            (r"(?:under|below|less than)\s+\$?(\d+(?:\.\d+)?)", "max_price"),
            (r"(?:over|above|more than)\s+\$?(\d+(?:\.\d+)?)", "min_price"),
        ]
        for pattern, key in price_patterns:
            match = re.search(pattern, lowered)
            if match:
                filters[key] = float(match.group(1))

        keyword_filters = [
            (("shoe", "shoes", "sneaker", "sneakers", "footwear", "slide", "trainer"), {"category": "footwear"}),
            (("jacket", "shell", "outerwear", "vest", "windbreaker", "puffer", "fleece"), {"category": "outerwear"}),
            (("legging", "leggings", "shorts", "jogger", "joggers", "pants", "bike shorts"), {"category": "bottoms"}),
            (("tee", "shirt", "tank", "hoodie", "top", "tops", "base layer"), {"category": "tops"}),
            (("beanie", "hat", "glove", "gloves", "belt", "strap", "accessory", "accessories"), {"category": "accessories"}),
            (("running",), {"activity": "running"}),
            (("trail running",), {"activity": "trail running"}),
            (("hiking",), {"activity": "hiking"}),
            (("yoga",), {"activity": "yoga"}),
            (("pilates",), {"activity": "pilates"}),
            (("cycling", "bike"), {"activity": "cycling"}),
            (("hiit",), {"activity": "hiit"}),
            (("gym", "lifting", "training"), {"activity": "training"}),
            (("walking",), {"activity": "walking"}),
            (("travel",), {"activity": "travel"}),
            (("camping",), {"activity": "camping"}),
            (("recovery",), {"activity": "recovery"}),
            (("women", "women's", "female"), {"gender": "women"}),
            (("men", "men's", "male"), {"gender": "men"}),
            (("unisex",), {"gender": "unisex"}),
            (("black",), {"color": "black"}),
            (("blue", "navy"), {"color": "blue"}),
            (("green", "sage", "olive"), {"color": "green"}),
            (("gray", "grey", "silver"), {"color": "gray"}),
            (("pink", "rose", "plum", "coral"), {"color": "pink"}),
            (("white", "cream", "stone", "sand"), {"color": "white"}),
            (("winter",), {"season": "winter"}),
            (("summer",), {"season": "summer"}),
            (("spring",), {"season": "spring"}),
            (("fall", "autumn"), {"season": "fall"}),
        ]

        for keywords, values in keyword_filters:
            if any(self._contains_keyword(lowered, keyword) for keyword in keywords):
                self._merge_filters(filters, values)

        return filters

    def _infer_image_filters(self, image_description: str) -> dict[str, Any]:
        text = image_description.lower()
        inferred = self.infer_filters_from_text(text)

        extra_keyword_filters = [
            (("running shoe", "road running", "daily trainer"), {"subcategory": "running shoes"}),
            (("trail shoe", "trail runner"), {"subcategory": "trail shoes"}),
        ]
        for keywords, values in extra_keyword_filters:
            if any(self._contains_keyword(text, keyword) for keyword in keywords):
                self._merge_filters(inferred, values)
        return inferred

    def _contains_keyword(self, text: str, keyword: str) -> bool:
        pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
        return re.search(pattern, text) is not None

    def _merge_filters(self, current: dict[str, Any], incoming: dict[str, Any]) -> None:
        for key, value in incoming.items():
            current.setdefault(key, value)

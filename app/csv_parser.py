from __future__ import annotations

import csv
import re
from io import StringIO
from typing import Any


def _normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _pick(row: dict[str, str], *candidates: str) -> str:
    normalized = {_normalize_key(k): (v or "").strip() for k, v in row.items()}
    for candidate in candidates:
        value = normalized.get(_normalize_key(candidate), "")
        if value:
            return value
    return ""


def _parse_float(value: str, default: float = 0.0) -> float:
    if not value:
        return default
    cleaned = re.sub(r"[^0-9.]+", "", value)
    if not cleaned:
        return default
    try:
        return float(cleaned)
    except ValueError:
        return default


def _split_list(value: str, fallback: list[str]) -> list[str]:
    if not value:
        return fallback
    parts = [part.strip() for part in re.split(r"[|,;/]", value) if part.strip()]
    return parts or fallback


def parse_catalog_csv(csv_text: str, slug_prefix: str = "upload") -> list[dict[str, Any]]:
    reader = csv.DictReader(StringIO(csv_text))
    products: list[dict[str, Any]] = []

    for idx, row in enumerate(reader, start=1):
        name = _pick(row, "name", "product", "product_name", "title", "item", "item_name")
        if not name:
            name = f"Imported Item {idx}"

        description = _pick(row, "description", "details", "summary")
        if not description:
            description = f"Imported catalog item: {name}."

        category = _pick(row, "category", "type", "department") or "general"
        subcategory = _pick(row, "subcategory", "sub_category", "subtype") or "general"
        brand = _pick(row, "brand", "maker", "vendor") or "Unknown Brand"
        color = _pick(row, "color", "colour") or "unspecified"
        material = _pick(row, "material", "fabric") or "unspecified"
        fit = _pick(row, "fit", "size_type", "style") or "regular"
        gender = _pick(row, "gender", "audience") or "unisex"

        products.append(
            {
                "id": f"{slug_prefix}_{idx:03d}",
                "name": name,
                "brand": brand,
                "category": category.lower().strip(),
                "subcategory": subcategory.lower().strip(),
                "description": description.strip(),
                "price": _parse_float(_pick(row, "price", "cost", "amount", "msrp"), default=0.0),
                "gender": gender.lower().strip(),
                "activity": _split_list(_pick(row, "activity", "activities", "use_case"), ["general"]),
                "fit": fit.lower().strip(),
                "material": material.lower().strip(),
                "color": color.lower().strip(),
                "season": _split_list(_pick(row, "season", "seasons"), ["all"]),
                "tags": _split_list(_pick(row, "tags", "keywords"), ["imported"]),
                "image_path": _pick(row, "image_path", "image", "image_url") or "/static/images/accessories.png",
                "reviews": [
                    {"text": "Imported from uploaded CSV catalog.", "rating": 4},
                ],
            }
        )

    return products

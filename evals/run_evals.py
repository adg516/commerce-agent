from __future__ import annotations

import base64
import json
import os
import time
import uuid
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_PATH = BASE_DIR / "evals" / "prompts.json"
CATALOG_PATH = BASE_DIR / "data" / "catalog.json"
API_URL = os.getenv("COMMERCE_AGENT_URL", "http://127.0.0.1:8000") + "/api/chat"


def load_catalog_ids() -> set[str]:
    products = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {product["id"] for product in products}


def image_to_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def main() -> None:
    prompts = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    valid_ids = load_catalog_ids()

    passed = 0
    for prompt in prompts:
        payload = {
            "message": prompt["message"],
            "conversation_id": f"{prompt['name']}-{uuid.uuid4()}",
        }
        if prompt.get("image_path"):
            payload["image_b64"] = image_to_b64(BASE_DIR / prompt["image_path"])

        started = time.perf_counter()
        response = requests.post(API_URL, json=payload, timeout=60)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        body = response.json()

        product_ids = {product["id"] for product in body.get("products", [])}
        invalid_ids = sorted(product_ids - valid_ids)
        has_products = bool(product_ids)
        expected_products = prompt["expects_products"]

        ok = response.ok and not invalid_ids and has_products == expected_products
        passed += int(ok)

        print(
            f"[{'PASS' if ok else 'FAIL'}] {prompt['name']} "
            f"status={response.status_code} products={len(product_ids)} latency_ms={elapsed_ms}"
        )
        if invalid_ids:
            print(f"  invalid product ids: {invalid_ids}")
        if has_products != expected_products:
            print(f"  expected_products={expected_products} actual_products={has_products}")

    print(f"\nPassed {passed}/{len(prompts)} evals")


if __name__ == "__main__":
    main()

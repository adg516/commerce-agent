from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from openai import OpenAI

from app.config import Settings, get_settings
from app.models import Product, Source
from app.tools import CatalogTools

_CONVERSATION_TTL = 1800  # 30 minutes
_MAX_CONVERSATIONS = 500


SYSTEM_PROMPT = """
You are a helpful commerce assistant working across one or more product catalogs.
Respect the selected catalog context for each user request.

Rules:
- Be concise and conversational.
- The product cards are shown to the user separately in the UI with full details (price, image, tags). Do NOT repeat product attributes (price, material, color) in your message.
- When mentioning multiple products, use a short bulleted list with the **actual product name** from tool results and a brief reason it fits (one line each). Keep it scannable.
- Add a one-sentence intro before the list and optionally a one-sentence closing offer to help further.
- Always search the catalog before answering product questions. Never suggest generic product categories — only reference specific products returned by your tools.
- If a query is clearly outside the selected catalog domain (e.g. asking for headphones in a home catalog), say you don't carry that product type in the current catalog and suggest the user switch catalogs. Do NOT recommend unrelated products as substitutes.
- Only recommend products that come from tool results. Never invent product names, IDs, prices, reviews, or availability.
- If the user asks for recommendations, search first and make reasonable assumptions rather than asking clarifying questions.
- For general chat (greetings, capability questions), answer normally without forcing product recommendations.
- If an image was provided, rely on the supplied image description and the image search tool instead of guessing.
- If tool results contain reasonable matches, recommend the best available options instead of saying nothing was found.
""".strip()


@dataclass
class AgentResult:
    reply: str
    conversation_id: str
    products: list[Product]
    sources: list[Source]
    metadata: dict[str, Any]


class CommerceAgent:
    # SCALE: inject a metrics client here (e.g. prometheus_client, Datadog statsd)
    # to track request counts, latencies, tool call distributions, and error rates.
    # Example: self.metrics = MetricsClient(namespace="commerce_agent")

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None
        self.tools = CatalogTools(self.settings)
        self._lock = threading.Lock()
        # SCALE: replace in-memory conversation store with Redis or a database
        # (e.g. Redis HSET keyed by conversation_id, PostgreSQL jsonb column).
        # This enables horizontal scaling across multiple pods/workers.
        self._conversations: dict[str, list[dict[str, Any]]] = {}
        self._last_access: dict[str, float] = {}

    def _get_history(self, conversation_id: str) -> list[dict[str, Any]]:
        # SCALE: fetch from Redis/DB instead of local dict.
        # e.g. redis.hget(f"conv:{conversation_id}", "messages")
        with self._lock:
            self._last_access[conversation_id] = time.time()
            return list(self._conversations.get(conversation_id, []))

    def _save_history(self, conversation_id: str, messages: list[dict[str, Any]]) -> None:
        # SCALE: persist to Redis/DB with TTL instead of in-memory eviction.
        # e.g. redis.hset(f"conv:{conversation_id}", "messages", json.dumps(messages[-12:]))
        #      redis.expire(f"conv:{conversation_id}", _CONVERSATION_TTL)
        with self._lock:
            self._conversations[conversation_id] = messages[-12:]
            self._last_access[conversation_id] = time.time()
            self._evict_stale()

    def _evict_stale(self) -> None:
        """Remove expired or overflow conversations. Caller must hold self._lock."""
        now = time.time()
        expired = [cid for cid, ts in self._last_access.items() if now - ts > _CONVERSATION_TTL]
        for cid in expired:
            self._conversations.pop(cid, None)
            self._last_access.pop(cid, None)
        if len(self._conversations) > _MAX_CONVERSATIONS:
            oldest = sorted(self._last_access, key=self._last_access.get)
            for cid in oldest[: len(self._conversations) - _MAX_CONVERSATIONS]:
                self._conversations.pop(cid, None)
                self._last_access.pop(cid, None)

    def chat(
        self,
        message: str,
        image_b64: str | None = None,
        conversation_id: str | None = None,
        catalog_slug: str = "all",
    ) -> AgentResult:
        # SCALE: emit metric for chat request received.
        # e.g. self.metrics.increment("chat.request", tags={"catalog": catalog_slug})
        conversation_id = conversation_id or str(uuid4())
        history = self._get_history(conversation_id)
        tool_products: dict[str, Product] = {}
        tool_sources: list[Source] = []
        image_description: str | None = None

        user_content = message.strip() or "Help me browse the catalog."

        if not self.client:
            fallback_reply = (
                "The app is set up, but an OpenAI API key is still needed for the full agent flow. "
                "Once `OPENAI_API_KEY` is configured, I can search the catalog semantically and handle image search."
            )
            self._save_history(conversation_id, [*history, {"role": "user", "content": user_content}])
            return AgentResult(
                reply=fallback_reply,
                conversation_id=conversation_id,
                products=[],
                sources=tool_sources,
                metadata={"mode": "missing_api_key"},
            )

        if image_b64:
            image_description = self.tools.describe_image(image_b64=image_b64, user_prompt=user_content)
            user_content = (
                f"{user_content}\n\n"
                f"Uploaded image description for search: {image_description}"
            )
            tool_sources.append(Source(kind="image_description", detail=image_description))

        if catalog_slug and catalog_slug != "all":
            user_content = f"{user_content}\n\nUse catalog: {catalog_slug}"

        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
        messages.append({"role": "user", "content": user_content})

        for _ in range(4):
            # SCALE: wrap this call with latency tracking and token-usage metrics.
            # e.g. self.metrics.timer("openai.chat.latency").start()
            # SCALE: for high throughput, queue chat requests via a task broker
            # (Celery, RQ, or pub/sub like Redis Streams / Kafka) and return a
            # job ID so the frontend can poll or receive results via WebSocket.
            response = self.client.chat.completions.create(
                model=self.settings.openai_chat_model,
                temperature=0,
                messages=messages,
                tools=self._tool_definitions(),
                tool_choice="auto",
            )
            # SCALE: log token usage for cost monitoring.
            # e.g. self.metrics.increment("openai.tokens.prompt", response.usage.prompt_tokens)
            #      self.metrics.increment("openai.tokens.completion", response.usage.completion_tokens)

            assistant_message = response.choices[0].message
            assistant_payload: dict[str, Any] = {
                "role": "assistant",
                "content": assistant_message.content or "",
            }

            if assistant_message.tool_calls:
                assistant_payload["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in assistant_message.tool_calls
                ]

            messages.append(assistant_payload)

            if not assistant_message.tool_calls:
                if not tool_products and self._should_force_search(message=message, image_description=image_description):
                    fallback_result = self._run_fallback_search(
                        message=message,
                        image_description=image_description,
                        catalog_slug=catalog_slug,
                    )
                    tool_sources.append(Source(kind="fallback_search", detail=self._source_detail(fallback_result)))
                    self._merge_products(tool_products, fallback_result, catalog_slug=catalog_slug, min_score=0.3)
                    if tool_products:
                        self._save_history(conversation_id, messages[1:])
                        return AgentResult(
                            reply=self._build_fallback_reply(list(tool_products.values())),
                            conversation_id=conversation_id,
                            products=list(tool_products.values()),
                            sources=tool_sources,
                            metadata={"image_description": image_description, "mode": "fallback_search"},
                        )

                final_reply = assistant_message.content or "I found a few options for you."
                self._save_history(conversation_id, messages[1:])
                return AgentResult(
                    reply=final_reply,
                    conversation_id=conversation_id,
                    products=list(tool_products.values()),
                    sources=tool_sources,
                    metadata={"image_description": image_description},
                )

            for tool_call in assistant_message.tool_calls:
                # SCALE: emit per-tool metrics (call count, latency, error rate).
                # e.g. self.metrics.increment("tool.call", tags={"tool": tool_call.function.name})
                result = self._run_tool(
                    tool_call.function.name,
                    tool_call.function.arguments,
                    catalog_slug=catalog_slug,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )
                tool_sources.append(Source(kind=tool_call.function.name, detail=self._source_detail(result)))
                self._merge_products(tool_products, result, catalog_slug=catalog_slug)

        self._save_history(conversation_id, messages[1:])
        return AgentResult(
            reply="I gathered some catalog context, but the response loop took too long. Please try again.",
            conversation_id=conversation_id,
            products=list(tool_products.values()),
            sources=tool_sources,
            metadata={"image_description": image_description, "mode": "loop_timeout"},
        )

    def _merge_products(
        self,
        tool_products: dict[str, Product],
        result: dict[str, Any],
        catalog_slug: str = "all",
        min_score: float = 0.0,
    ) -> None:
        if "matches" in result:
            for match in result["matches"]:
                if catalog_slug != "all" and match.get("catalog_slug") and match["catalog_slug"] != catalog_slug:
                    continue
                if min_score and float(match.get("score", 0)) < min_score:
                    continue
                product = Product.model_validate(match["product"])
                tool_products[product.id] = product
        elif "product" in result and isinstance(result["product"], dict):
            product = Product.model_validate(result["product"])
            tool_products[product.id] = product

    def _source_detail(self, result: dict[str, Any]) -> str:
        prefix = ""
        if result.get("catalog_slug"):
            prefix = f"catalog={result['catalog_slug']} "
        if "query" in result:
            return f"{prefix}query={result['query']}".strip()
        if "image_description" in result:
            return f"{prefix}image_description={result['image_description']}".strip()
        if "product_id" in result:
            return f"{prefix}product_id={result['product_id']}".strip()
        if "product" in result and isinstance(result["product"], dict):
            return f"{prefix}product_id={result['product']['id']}".strip()
        return (prefix + "tool_result").strip()

    def _run_tool(self, name: str, raw_arguments: str, catalog_slug: str = "all") -> dict[str, Any]:
        arguments = json.loads(raw_arguments or "{}")
        arguments["catalog_slug"] = catalog_slug

        if name == "list_catalogs":
            return self.tools.list_catalogs()
        if name == "search_catalog_text":
            return self.tools.search_catalog_text(**arguments)
        if name == "search_catalog_image":
            return self.tools.search_catalog_image(**arguments)
        if name == "get_product":
            return self.tools.get_product(**arguments)
        if name == "get_reviews":
            return self.tools.get_reviews(**arguments)

        return {"error": f"Unknown tool: {name}"}

    def _should_force_search(self, message: str, image_description: str | None) -> bool:
        if image_description:
            return True

        lowered = message.lower()
        if lowered.strip().startswith("can you ") or "what can you" in lowered or "do you support" in lowered:
            return False

        shopping_keywords = (
            "recommend",
            "show me",
            "find",
            "need",
            "looking for",
            "search",
            "something for",
            "under $",
            "best",
            "what should i get",
            "what should i wear",
            "should i wear",
            "help me choose",
            "shirt",
            "top",
            "shoe",
            "pant",
            "legging",
            "jacket",
            "short",
            "sock",
            "jogger",
            "tank",
            "bra",
            "hoodie",
            "wear to",
            "wear for",
            "good for",
            "suggestions",
            "options",
            "recs",
            "product",
            "catalog",
            "what do you have",
            "what have you got",
            "browse",
            "picnic",
            "outfit",
            "gear",
            "activewear",
            "athleisure",
        )
        return any(keyword in lowered for keyword in shopping_keywords)

    def _run_fallback_search(
        self,
        message: str,
        image_description: str | None,
        catalog_slug: str = "all",
    ) -> dict[str, Any]:
        if image_description:
            return self.tools.search_catalog_image(
                image_description=image_description,
                filters=self.tools.infer_filters_from_text(message),
                top_k=4,
                catalog_slug=catalog_slug,
            )
        return self.tools.search_catalog_text(
            query=message,
            filters=self.tools.infer_filters_from_text(message),
            top_k=4,
            catalog_slug=catalog_slug,
        )

    def _build_fallback_reply(self, products: list[Product]) -> str:
        top = products[:4]
        lines = ["Here are some picks from the catalog:"]
        for p in top:
            lines.append(f"- **{p.name}** — {p.description.split('.')[0].strip()}.")
        lines.append("\nCheck out the cards below for full details. I can narrow these by budget, activity, color, or fit.")
        return "\n".join(lines)

    def _tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_catalogs",
                    "description": "List available catalogs the user can search.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_catalog_text",
                    "description": "Search a catalog using a natural language query plus optional filters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "category": {"type": "string"},
                                    "subcategory": {"type": "string"},
                                    "gender": {"type": "string"},
                                    "activity": {"type": "string"},
                                    "color": {"type": "string"},
                                    "season": {"type": "string"},
                                    "min_price": {"type": "number"},
                                    "max_price": {"type": "number"},
                                },
                                "additionalProperties": False,
                            },
                            "top_k": {"type": "integer", "minimum": 1, "maximum": 8},
                        },
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_catalog_image",
                    "description": "Search a catalog using an already-generated text description of the uploaded image.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_description": {"type": "string"},
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "category": {"type": "string"},
                                    "subcategory": {"type": "string"},
                                    "gender": {"type": "string"},
                                    "activity": {"type": "string"},
                                    "color": {"type": "string"},
                                    "season": {"type": "string"},
                                    "min_price": {"type": "number"},
                                    "max_price": {"type": "number"},
                                },
                                "additionalProperties": False,
                            },
                            "top_k": {"type": "integer", "minimum": 1, "maximum": 8},
                        },
                        "required": ["image_description"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_product",
                    "description": "Get full product details for a single product ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                        },
                        "required": ["product_id"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_reviews",
                    "description": "Get review snippets and average rating for a product ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                        },
                        "required": ["product_id"],
                        "additionalProperties": False,
                    },
                },
            },
        ]

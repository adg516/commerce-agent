from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from openai import OpenAI

from app.config import Settings, get_settings
from app.models import Product, Source
from app.tools import CatalogTools


SYSTEM_PROMPT = """
You are a helpful commerce assistant for an athletic and activewear store.
The catalog only contains sportswear, athleisure, and workout gear.

Rules:
- Be concise and conversational. Keep replies to 2-3 short sentences.
- The product cards are shown to the user separately in the UI with full details (price, image, tags). Do NOT repeat product attributes in your message. Just say why the matches fit in plain language and let the cards do the rest. Never use numbered lists or bullet points of products.
- If a query is outside the athletic/activewear domain (e.g. "date outfit", "formal wear"), acknowledge that the catalog is focused on sportswear and athleisure, then suggest the closest versatile or crossover pieces.
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
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None
        self.tools = CatalogTools(self.settings)
        self._conversations: dict[str, list[dict[str, Any]]] = {}

    def chat(self, message: str, image_b64: str | None = None, conversation_id: str | None = None) -> AgentResult:
        conversation_id = conversation_id or str(uuid4())
        history = list(self._conversations.get(conversation_id, []))
        tool_products: dict[str, Product] = {}
        tool_sources: list[Source] = []
        image_description: str | None = None

        user_content = message.strip() or "Help me browse the catalog."

        if not self.client:
            fallback_reply = (
                "The app is set up, but an OpenAI API key is still needed for the full agent flow. "
                "Once `OPENAI_API_KEY` is configured, I can search the catalog semantically and handle image search."
            )
            self._conversations[conversation_id] = [*history, {"role": "user", "content": user_content}][-12:]
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

        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
        messages.append({"role": "user", "content": user_content})

        for _ in range(4):
            response = self.client.chat.completions.create(
                model=self.settings.openai_chat_model,
                temperature=0,
                messages=messages,
                tools=self._tool_definitions(),
                tool_choice="auto",
            )

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
                    )
                    tool_sources.append(Source(kind="fallback_search", detail=self._source_detail(fallback_result)))
                    self._merge_products(tool_products, fallback_result)
                    if tool_products:
                        self._conversations[conversation_id] = messages[1:][-12:]
                        return AgentResult(
                            reply=self._build_fallback_reply(list(tool_products.values())),
                            conversation_id=conversation_id,
                            products=list(tool_products.values()),
                            sources=tool_sources,
                            metadata={"image_description": image_description, "mode": "fallback_search"},
                        )

                final_reply = assistant_message.content or "I found a few options for you."
                self._conversations[conversation_id] = messages[1:][-12:]
                return AgentResult(
                    reply=final_reply,
                    conversation_id=conversation_id,
                    products=list(tool_products.values()),
                    sources=tool_sources,
                    metadata={"image_description": image_description},
                )

            for tool_call in assistant_message.tool_calls:
                result = self._run_tool(tool_call.function.name, tool_call.function.arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )
                tool_sources.append(Source(kind=tool_call.function.name, detail=self._source_detail(result)))
                self._merge_products(tool_products, result)

        self._conversations[conversation_id] = messages[1:][-12:]
        return AgentResult(
            reply="I gathered some catalog context, but the response loop took too long. Please try again.",
            conversation_id=conversation_id,
            products=list(tool_products.values()),
            sources=tool_sources,
            metadata={"image_description": image_description, "mode": "loop_timeout"},
        )

    def _merge_products(self, tool_products: dict[str, Product], result: dict[str, Any]) -> None:
        if "matches" in result:
            for match in result["matches"]:
                product = Product.model_validate(match["product"])
                tool_products[product.id] = product
        elif "product" in result and isinstance(result["product"], dict):
            product = Product.model_validate(result["product"])
            tool_products[product.id] = product

    def _source_detail(self, result: dict[str, Any]) -> str:
        if "query" in result:
            return f"query={result['query']}"
        if "image_description" in result:
            return f"image_description={result['image_description']}"
        if "product_id" in result:
            return f"product_id={result['product_id']}"
        if "product" in result and isinstance(result["product"], dict):
            return f"product_id={result['product']['id']}"
        return "tool_result"

    def _run_tool(self, name: str, raw_arguments: str) -> dict[str, Any]:
        arguments = json.loads(raw_arguments or "{}")

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
        )
        return any(keyword in lowered for keyword in shopping_keywords)

    def _run_fallback_search(self, message: str, image_description: str | None) -> dict[str, Any]:
        if image_description:
            return self.tools.search_catalog_image(
                image_description=image_description,
                filters=self.tools.infer_filters_from_text(message),
                top_k=4,
            )
        return self.tools.search_catalog_text(
            query=message,
            filters=self.tools.infer_filters_from_text(message),
            top_k=4,
        )

    def _build_fallback_reply(self, products: list[Product]) -> str:
        top_products = products[:3]
        lines = ["Here are the closest catalog matches I found:"]
        for product in top_products:
            lines.append(
                f"- {product.name} by {product.brand} for ${product.price:.2f}: "
                f"{product.description}"
            )
        lines.append("If you want, I can narrow these down by budget, activity, color, or fit.")
        return "\n".join(lines)

    def _tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_catalog_text",
                    "description": "Search the predefined athletic catalog using a natural language query plus optional filters.",
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
                    "description": "Search the catalog using an already-generated text description of the uploaded image.",
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

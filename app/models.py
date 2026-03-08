from typing import Any

from pydantic import BaseModel, Field


class Review(BaseModel):
    text: str
    rating: int = Field(ge=1, le=5)


class Product(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    subcategory: str
    description: str
    price: float
    gender: str
    activity: list[str]
    fit: str
    material: str
    color: str
    season: list[str]
    tags: list[str]
    image_path: str
    reviews: list[Review]


class ChatRequest(BaseModel):
    message: str = ""
    image_b64: str | None = None
    conversation_id: str | None = None


class Source(BaseModel):
    kind: str
    detail: str


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    products: list[Product]
    sources: list[Source] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

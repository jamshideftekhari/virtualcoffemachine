from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class BrewRequest(BaseModel):
    beverage_id: str = Field(..., examples=["espresso"])


class BrewResponse(BaseModel):
    brew_order_id: UUID
    beverage_id: str
    status: str


class BeverageItem(BaseModel):
    beverage_id: str
    name: str


class BeverageListResponse(BaseModel):
    beverages: list[BeverageItem]

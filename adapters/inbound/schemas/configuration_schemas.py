from __future__ import annotations

from pydantic import BaseModel, Field


class ThresholdUpdate(BaseModel):
    low: float = Field(..., gt=0)


class RecipeUpdate(BaseModel):
    name: str
    requirements: dict[str, float] = Field(
        ..., description="container_id -> amount in the container's unit"
    )


class ConfigurationPayload(BaseModel):
    waste_full_threshold: int | None = Field(None, ge=1)
    thresholds: dict[str, ThresholdUpdate] | None = None
    recipes: dict[str, RecipeUpdate] | None = None


class RecipeResponse(BaseModel):
    beverage_id: str
    name: str
    requirements: dict[str, float]


class ThresholdResponse(BaseModel):
    container_id: str
    low: float
    unit: str


class ConfigurationResponse(BaseModel):
    source: str
    waste_full_threshold: int
    recipes: list[RecipeResponse]
    thresholds: list[ThresholdResponse]


class ConfigResultResponse(BaseModel):
    status: str
    source: str
    reason: str | None = None

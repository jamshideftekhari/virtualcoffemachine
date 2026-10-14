from __future__ import annotations

from pydantic import BaseModel, Field


class ContainerStateResponse(BaseModel):
    container_id: str
    level: float
    unit: str
    max_capacity: float
    low_threshold: float
    state: str


class WasteStateResponse(BaseModel):
    brew_count: int
    full_threshold: int
    state: str


class AllContainersResponse(BaseModel):
    ingredients: list[ContainerStateResponse]
    waste: WasteStateResponse


class FillRequest(BaseModel):
    target_level: float = Field(..., gt=0, description="Target fill level in the container's unit")

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.model.value_objects import ContainerState, MachineState, WasteState


@dataclass(frozen=True)
class BrewResult:
    brew_order_id: UUID
    beverage_id: str
    status: str  # "completed"


@dataclass(frozen=True)
class ContainerStateView:
    container_id: str
    level: float
    unit: str
    max_capacity: float
    low_threshold: float
    state: ContainerState


@dataclass(frozen=True)
class WasteStateView:
    brew_count: int
    full_threshold: int
    state: WasteState


@dataclass(frozen=True)
class RecipeView:
    beverage_id: str
    name: str
    requirements: dict[str, float]  # container_id -> amount value


@dataclass(frozen=True)
class ThresholdView:
    container_id: str
    low: float
    unit: str


@dataclass(frozen=True)
class ConfigurationView:
    source: str  # "remote" | "default"
    waste_full_threshold: int
    recipes: list[RecipeView]
    thresholds: list[ThresholdView]


@dataclass(frozen=True)
class ConfigResult:
    status: str   # "accepted" | "rejected"
    source: str
    reason: str | None = None


@dataclass(frozen=True)
class MachineStateView:
    state: MachineState

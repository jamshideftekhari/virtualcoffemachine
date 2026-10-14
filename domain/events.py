from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.model.value_objects import ContainerId, MachineState, Quantity


# ---------------------------------------------------------------------------
# Container events
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ContainerFilled:
    container_id: ContainerId
    new_level: Quantity


@dataclass(frozen=True)
class ContainerLevelChanged:
    container_id: ContainerId
    new_level: Quantity


@dataclass(frozen=True)
class ContainerLow:
    container_id: ContainerId
    current_level: Quantity
    low_threshold: Quantity


@dataclass(frozen=True)
class ContainerEmpty:
    container_id: ContainerId


# ---------------------------------------------------------------------------
# Waste container events
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WasteContainerUpdated:
    brew_count: int
    full_threshold: int


@dataclass(frozen=True)
class WasteContainerFull:
    brew_count: int
    full_threshold: int


@dataclass(frozen=True)
class WasteContainerEmptied:
    pass


# ---------------------------------------------------------------------------
# Brew events
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrewStarted:
    brew_order_id: UUID
    beverage_id: str


@dataclass(frozen=True)
class BrewCompleted:
    brew_order_id: UUID
    beverage_id: str


@dataclass(frozen=True)
class BrewAborted:
    brew_order_id: UUID
    beverage_id: str
    reason: str
    container_id: ContainerId | None = None


@dataclass(frozen=True)
class BrewRejected:
    beverage_id: str
    reason: str
    container_id: ContainerId | None = None


# ---------------------------------------------------------------------------
# Machine state events
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MachineStateChanged:
    from_state: MachineState
    to_state: MachineState


# ---------------------------------------------------------------------------
# Configuration events
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConfigurationApplied:
    source: str  # "remote" | "default"


@dataclass(frozen=True)
class ConfigurationRejected:
    reason: str

from __future__ import annotations

from dataclasses import dataclass

from domain.events import (
    WasteContainerEmptied,
    WasteContainerFull,
    WasteContainerUpdated,
)
from domain.exceptions import WasteContainerFullError
from domain.model.value_objects import WasteState

DomainEvent = WasteContainerUpdated | WasteContainerFull | WasteContainerEmptied


@dataclass
class WasteContainer:
    """
    Aggregate root for the waste container.

    Tracked by brew count, not by volume.

    Invariants:
    - brew_count is in range [0, full_threshold]
    - Brewing is blocked when state is FULL
    """

    brew_count: int
    full_threshold: int

    def __post_init__(self) -> None:
        if self.full_threshold < 1:
            raise ValueError("full_threshold must be >= 1")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def state(self) -> WasteState:
        if self.brew_count == 0:
            return WasteState.EMPTY
        if self.brew_count >= self.full_threshold:
            return WasteState.FULL
        return WasteState.NORMAL

    def is_full(self) -> bool:
        return self.state == WasteState.FULL

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def increment(self) -> list[DomainEvent]:
        """Record one brew worth of waste. Raises if already full."""
        if self.is_full():
            raise WasteContainerFullError(self.brew_count, self.full_threshold)

        self.brew_count += 1
        events: list[DomainEvent] = [
            WasteContainerUpdated(self.brew_count, self.full_threshold)
        ]
        if self.is_full():
            events.append(WasteContainerFull(self.brew_count, self.full_threshold))
        return events

    def empty(self) -> list[DomainEvent]:
        """Reset waste count to zero."""
        self.brew_count = 0
        return [WasteContainerEmptied()]

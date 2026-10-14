from __future__ import annotations

from dataclasses import dataclass, field

from domain.events import (
    ContainerEmpty,
    ContainerFilled,
    ContainerLevelChanged,
    ContainerLow,
)
from domain.exceptions import ExceedsMaxCapacity, InsufficientIngredient
from domain.model.value_objects import ContainerId, ContainerState, Quantity

DomainEvent = ContainerFilled | ContainerLevelChanged | ContainerLow | ContainerEmpty


@dataclass
class Container:
    """
    Aggregate root for a single ingredient container.

    Invariants:
    - level is in range [0, max_capacity]
    - state is derived from level vs thresholds (never set directly)
    """

    id: ContainerId
    level: Quantity
    max_capacity: Quantity
    low_threshold: Quantity

    def __post_init__(self) -> None:
        if self.low_threshold >= self.max_capacity:
            raise ValueError(
                f"low_threshold {self.low_threshold} must be less than "
                f"max_capacity {self.max_capacity}"
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def state(self) -> ContainerState:
        if self.level.value <= 0:
            return ContainerState.EMPTY
        if self.level < self.low_threshold:
            return ContainerState.LOW
        return ContainerState.NORMAL

    def has_sufficient(self, amount: Quantity) -> bool:
        return self.level >= amount

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def fill(self, target: Quantity) -> list[DomainEvent]:
        """Set the container level to target. Must not exceed max_capacity."""
        if target > self.max_capacity:
            raise ExceedsMaxCapacity(self.id, target, self.max_capacity)

        self.level = target
        events: list[DomainEvent] = [ContainerFilled(self.id, self.level)]
        events.extend(self._state_events())
        return events

    def deduct(self, amount: Quantity) -> list[DomainEvent]:
        """
        Deduct amount from the container level.

        Raises InsufficientIngredient if amount exceeds current level.
        The use case pre-checks before calling this, but the domain
        enforces the invariant defensively.
        """
        if not self.has_sufficient(amount):
            raise InsufficientIngredient(self.id, amount, self.level)

        self.level = self.level - amount
        events: list[DomainEvent] = [ContainerLevelChanged(self.id, self.level)]
        events.extend(self._state_events())
        return events

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _state_events(self) -> list[DomainEvent]:
        if self.state == ContainerState.EMPTY:
            return [ContainerEmpty(self.id)]
        if self.state == ContainerState.LOW:
            return [ContainerLow(self.id, self.level, self.low_threshold)]
        return []

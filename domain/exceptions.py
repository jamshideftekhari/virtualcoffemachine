from __future__ import annotations

from domain.model.value_objects import ContainerId, MachineState, Quantity


class DomainException(Exception):
    """Base class for all domain exceptions."""


class MachineNotReady(DomainException):
    def __init__(self, current_state: MachineState) -> None:
        self.current_state = current_state
        super().__init__(f"Machine is not ready — current state: {current_state.value}")


class InvalidStateTransition(DomainException):
    def __init__(self, from_state: MachineState, to_state: MachineState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid state transition: {from_state.value} → {to_state.value}"
        )


class InsufficientIngredient(DomainException):
    def __init__(
        self,
        container_id: ContainerId,
        required: Quantity,
        available: Quantity,
    ) -> None:
        self.container_id = container_id
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient {container_id.value}: required {required}, available {available}"
        )


class ExceedsMaxCapacity(DomainException):
    def __init__(
        self,
        container_id: ContainerId,
        target: Quantity,
        max_capacity: Quantity,
    ) -> None:
        self.container_id = container_id
        self.target = target
        self.max_capacity = max_capacity
        super().__init__(
            f"Target {target} exceeds max capacity {max_capacity} for {container_id.value}"
        )


class WasteContainerFullError(DomainException):
    def __init__(self, brew_count: int, threshold: int) -> None:
        self.brew_count = brew_count
        self.threshold = threshold
        super().__init__(
            f"Waste container is full: {brew_count}/{threshold} brews"
        )


class RecipeNotFound(DomainException):
    def __init__(self, beverage_id: str) -> None:
        self.beverage_id = beverage_id
        super().__init__(f"No recipe found for beverage: {beverage_id!r}")


class ConfigurationInvalidError(DomainException):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Configuration is invalid: {reason}")

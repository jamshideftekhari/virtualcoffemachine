from __future__ import annotations

from dataclasses import dataclass, field

from domain.model.value_objects import ContainerId, Quantity


@dataclass(frozen=True)
class RecipeRequirement:
    """How much of one ingredient is needed for a single serving."""

    container_id: ContainerId
    amount: Quantity


@dataclass(frozen=True)
class Recipe:
    """
    Defines the ingredients and quantities for one beverage.

    Invariants:
    - beverage_id is unique within the menu
    - requirements is non-empty
    - no duplicate container_ids within requirements
    """

    beverage_id: str
    name: str
    requirements: tuple[RecipeRequirement, ...]

    def __post_init__(self) -> None:
        if not self.requirements:
            raise ValueError(f"Recipe {self.beverage_id!r} must have at least one requirement")
        ids = [r.container_id for r in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Recipe {self.beverage_id!r} has duplicate container requirements")

    def requirement_for(self, container_id: ContainerId) -> Quantity | None:
        """Return the required amount for a given container, or None if not used."""
        for req in self.requirements:
            if req.container_id == container_id:
                return req.amount
        return None

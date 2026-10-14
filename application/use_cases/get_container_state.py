from __future__ import annotations

from domain.model.value_objects import ContainerId

from application.ports.container_repository import ContainerRepository
from application.use_cases.results import ContainerStateView, WasteStateView


class GetContainerState:
    """Query: return the current state of one ingredient container."""

    def __init__(self, containers: ContainerRepository) -> None:
        self._containers = containers

    def execute(self, container_id: ContainerId) -> ContainerStateView:
        c = self._containers.get(container_id)
        return ContainerStateView(
            container_id=c.id.value,
            level=c.level.value,
            unit=c.level.unit,
            max_capacity=c.max_capacity.value,
            low_threshold=c.low_threshold.value,
            state=c.state,
        )


class GetAllContainerStates:
    """Query: return the current state of all ingredient containers and the waste container."""

    def __init__(self, containers: ContainerRepository) -> None:
        self._containers = containers

    def execute(self) -> tuple[list[ContainerStateView], WasteStateView]:
        ingredient_views = [
            ContainerStateView(
                container_id=c.id.value,
                level=c.level.value,
                unit=c.level.unit,
                max_capacity=c.max_capacity.value,
                low_threshold=c.low_threshold.value,
                state=c.state,
            )
            for c in self._containers.list_ingredients()
        ]
        waste = self._containers.get_waste()
        waste_view = WasteStateView(
            brew_count=waste.brew_count,
            full_threshold=waste.full_threshold,
            state=waste.state,
        )
        return ingredient_views, waste_view

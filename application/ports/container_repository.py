from __future__ import annotations

from typing import Protocol

from domain.model.container import Container
from domain.model.value_objects import ContainerId
from domain.model.waste_container import WasteContainer


class ContainerRepository(Protocol):
    """Outbound port — persistence for Container and WasteContainer aggregates."""

    def get(self, container_id: ContainerId) -> Container:
        """Return the container for the given id. Raises KeyError if not found."""
        ...

    def get_waste(self) -> WasteContainer:
        """Return the waste container."""
        ...

    def save(self, container: Container) -> None:
        """Persist a container aggregate."""
        ...

    def save_waste(self, waste: WasteContainer) -> None:
        """Persist the waste container aggregate."""
        ...

    def list_ingredients(self) -> list[Container]:
        """Return all ingredient containers (excludes waste)."""
        ...

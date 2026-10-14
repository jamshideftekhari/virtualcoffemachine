from __future__ import annotations

from domain.model.container import Container
from domain.model.value_objects import ContainerId, Quantity
from domain.model.waste_container import WasteContainer


class InMemoryContainerRepository:
    """
    Driven adapter — stores Container and WasteContainer aggregates in memory.

    Seeded on startup from default_config.json via seed_from_config().
    """

    def __init__(self) -> None:
        self._containers: dict[ContainerId, Container] = {}
        self._waste: WasteContainer | None = None

    # ------------------------------------------------------------------
    # ContainerRepository protocol implementation
    # ------------------------------------------------------------------

    def get(self, container_id: ContainerId) -> Container:
        try:
            return self._containers[container_id]
        except KeyError:
            raise KeyError(f"Container not found: {container_id.value}")

    def get_waste(self) -> WasteContainer:
        if self._waste is None:
            raise RuntimeError("WasteContainer not seeded")
        return self._waste

    def save(self, container: Container) -> None:
        self._containers[container.id] = container

    def save_waste(self, waste: WasteContainer) -> None:
        self._waste = waste

    def list_ingredients(self) -> list[Container]:
        return list(self._containers.values())

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    @classmethod
    def seed_from_config(cls, config: dict) -> "InMemoryContainerRepository":
        """
        Create and seed a repository from the loaded default_config dict.

        Each container starts at its configured initial_level.
        The waste container starts empty.
        """
        repo = cls()

        for raw_id, cfg in config["containers"].items():
            container_id = ContainerId(raw_id)
            unit = cfg["unit"]
            repo.save(
                Container(
                    id=container_id,
                    level=Quantity(cfg["initial_level"], unit),
                    max_capacity=Quantity(cfg["max_capacity"], unit),
                    low_threshold=Quantity(cfg["low_threshold"], unit),
                )
            )

        repo.save_waste(
            WasteContainer(
                brew_count=0,
                full_threshold=config["waste_full_threshold"],
            )
        )

        return repo

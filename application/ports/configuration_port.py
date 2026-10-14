from __future__ import annotations

from typing import Protocol

from domain.model.recipe import Recipe
from domain.model.value_objects import ContainerId, Quantity


class ConfigurationPort(Protocol):
    """
    Outbound port — access to the active machine configuration.

    Two implementations exist:
    - DefaultConfigurationAdapter  (loads embedded default_config.json)
    - RemoteConfigurationAdapter   (v2 — pulls from remote config service)
    """

    def get_recipe(self, beverage_id: str) -> Recipe:
        """Return recipe for beverage_id. Raises RecipeNotFound if unknown."""
        ...

    def get_all_recipes(self) -> list[Recipe]:
        """Return all enabled recipes in the current configuration."""
        ...

    def get_low_threshold(self, container_id: ContainerId) -> Quantity:
        """Return the configured low-level threshold for a container."""
        ...

    def get_waste_full_threshold(self) -> int:
        """Return the brew-count threshold at which the waste container is considered full."""
        ...

    def apply(self, payload: dict) -> None:
        """
        Validate and apply a new configuration payload.

        Raises ConfigurationInvalidError on validation failure.
        The previous configuration remains active on failure.
        """
        ...

    def get_source(self) -> str:
        """Return 'remote' or 'default' to indicate the active config origin."""
        ...

from __future__ import annotations

import copy
import json
from pathlib import Path

from domain.exceptions import ConfigurationInvalidError, RecipeNotFound
from domain.model.recipe import Recipe, RecipeRequirement
from domain.model.value_objects import ContainerId, Quantity


class DefaultConfigurationAdapter:
    """
    Driven adapter — owns the active machine configuration.

    Loads from default_config.json on startup.
    Remote config payloads are merged in via apply(); the source
    switches from 'default' to 'remote' on first successful apply.
    Rolls back to the previous config on validation failure.
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._source = "default"

    @classmethod
    def load(cls, path: str | Path) -> "DefaultConfigurationAdapter":
        with open(path, encoding="utf-8") as fh:
            return cls(json.load(fh))

    # ------------------------------------------------------------------
    # ConfigurationPort protocol implementation
    # ------------------------------------------------------------------

    def get_recipe(self, beverage_id: str) -> Recipe:
        recipes = self._config.get("recipes", {})
        if beverage_id not in recipes:
            raise RecipeNotFound(beverage_id)
        return self._build_recipe(beverage_id, recipes[beverage_id])

    def get_all_recipes(self) -> list[Recipe]:
        return [
            self._build_recipe(bid, data)
            for bid, data in self._config.get("recipes", {}).items()
        ]

    def get_low_threshold(self, container_id: ContainerId) -> Quantity:
        cfg = self._config["containers"][container_id.value]
        return Quantity(cfg["low_threshold"], cfg["unit"])

    def get_waste_full_threshold(self) -> int:
        return self._config["waste_full_threshold"]

    def apply(self, payload: dict) -> None:
        """
        Validate and merge a remote config payload (all fields optional).
        Raises ConfigurationInvalidError without changing state on failure.
        """
        self._validate(payload)
        merged = copy.deepcopy(self._config)

        if "waste_full_threshold" in payload:
            merged["waste_full_threshold"] = payload["waste_full_threshold"]

        if "thresholds" in payload:
            for raw_id, values in payload["thresholds"].items():
                merged["containers"][raw_id]["low_threshold"] = values["low"]

        if "recipes" in payload:
            for bid, data in payload["recipes"].items():
                merged["recipes"][bid] = data

        self._config = merged
        self._source = "remote"

    def get_source(self) -> str:
        return self._source

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_recipe(self, beverage_id: str, data: dict) -> Recipe:
        requirements = []
        for raw_id, amount in data["requirements"].items():
            unit = self._config["containers"][raw_id]["unit"]
            requirements.append(
                RecipeRequirement(
                    container_id=ContainerId(raw_id),
                    amount=Quantity(amount, unit),
                )
            )
        return Recipe(
            beverage_id=beverage_id,
            name=data["name"],
            requirements=tuple(requirements),
        )

    def _validate(self, payload: dict) -> None:
        if "waste_full_threshold" in payload:
            val = payload["waste_full_threshold"]
            if not isinstance(val, int) or val < 1:
                raise ConfigurationInvalidError(
                    "waste_full_threshold must be an integer >= 1"
                )

        known_containers = set(self._config["containers"].keys())

        if "thresholds" in payload:
            for raw_id, values in payload["thresholds"].items():
                if raw_id not in known_containers:
                    raise ConfigurationInvalidError(
                        f"Unknown container in thresholds: {raw_id!r}"
                    )
                low = values.get("low")
                if low is None or not isinstance(low, (int, float)) or low <= 0:
                    raise ConfigurationInvalidError(
                        f"Threshold 'low' for {raw_id!r} must be a positive number"
                    )
                max_cap = self._config["containers"][raw_id]["max_capacity"]
                if low >= max_cap:
                    raise ConfigurationInvalidError(
                        f"Threshold 'low' ({low}) for {raw_id!r} must be less than "
                        f"max_capacity ({max_cap})"
                    )

        if "recipes" in payload:
            for bid, data in payload["recipes"].items():
                reqs = data.get("requirements", {})
                if not reqs:
                    raise ConfigurationInvalidError(
                        f"Recipe {bid!r} must have at least one requirement"
                    )
                for raw_id, amount in reqs.items():
                    if raw_id not in known_containers:
                        raise ConfigurationInvalidError(
                            f"Recipe {bid!r} references unknown container: {raw_id!r}"
                        )
                    if not isinstance(amount, (int, float)) or amount <= 0:
                        raise ConfigurationInvalidError(
                            f"Recipe {bid!r}: amount for {raw_id!r} must be a positive number"
                        )

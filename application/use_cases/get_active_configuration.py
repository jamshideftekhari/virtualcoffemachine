from __future__ import annotations

from domain.model.value_objects import ContainerId

from application.ports.configuration_port import ConfigurationPort
from application.use_cases.results import ConfigurationView, RecipeView, ThresholdView


class GetActiveConfiguration:
    """Query: return the currently active configuration (recipes, thresholds, source)."""

    def __init__(self, config: ConfigurationPort) -> None:
        self._config = config

    def execute(self) -> ConfigurationView:
        recipes = [
            RecipeView(
                beverage_id=r.beverage_id,
                name=r.name,
                requirements={
                    req.container_id.value: req.amount.value
                    for req in r.requirements
                },
            )
            for r in self._config.get_all_recipes()
        ]

        thresholds = [
            ThresholdView(
                container_id=cid.value,
                low=self._config.get_low_threshold(cid).value,
                unit=self._config.get_low_threshold(cid).unit,
            )
            for cid in ContainerId
        ]

        return ConfigurationView(
            source=self._config.get_source(),
            waste_full_threshold=self._config.get_waste_full_threshold(),
            recipes=recipes,
            thresholds=thresholds,
        )

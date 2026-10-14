from __future__ import annotations

from domain.exceptions import ConfigurationInvalidError
from domain.model.value_objects import ContainerId

from application.ports.configuration_port import ConfigurationPort
from application.ports.container_repository import ContainerRepository
from application.use_cases.results import ConfigResult


class ApplyConfiguration:
    """
    Use case: the remote config service pushes a new configuration payload.

    Validation and application are delegated to the ConfigurationPort.
    On success, container low_threshold values are updated immediately.
    On failure the previous (or default) configuration remains active.
    Config changes take effect on the next brew order.
    """

    def __init__(self, config: ConfigurationPort, containers: ContainerRepository) -> None:
        self._config = config
        self._containers = containers

    def execute(self, payload: dict) -> ConfigResult:
        try:
            self._config.apply(payload)
        except ConfigurationInvalidError as exc:
            return ConfigResult(status="rejected", source=self._config.get_source(), reason=exc.reason)

        # Propagate updated thresholds to existing container aggregates
        for container_id in ContainerId:
            try:
                container = self._containers.get(container_id)
                container.low_threshold = self._config.get_low_threshold(container_id)
                self._containers.save(container)
            except KeyError:
                pass

        return ConfigResult(status="accepted", source=self._config.get_source())

from __future__ import annotations

from domain.events import ContainerEmpty, ContainerLow
from domain.exceptions import ExceedsMaxCapacity
from domain.model.machine import CoffeeMachine
from domain.model.value_objects import ContainerId, MachineState, Quantity

from application.ports.alert_port import AlertPort
from application.ports.configuration_port import ConfigurationPort
from application.ports.container_repository import ContainerRepository
from application.ports.display_port import DisplayPort
from application.use_cases.results import ContainerStateView


class FillContainer:
    """
    Use case: an operator fills an ingredient container to a target level.

    Side effect: if the machine is in ERROR state (caused by an empty container),
    filling any ingredient container transitions the machine back to READY.
    """

    def __init__(
        self,
        containers: ContainerRepository,
        config: ConfigurationPort,
        machine: CoffeeMachine,
        alerts: AlertPort,
        display: DisplayPort,
    ) -> None:
        self._containers = containers
        self._config = config
        self._machine = machine
        self._alerts = alerts
        self._display = display

    def execute(self, container_id: ContainerId, target_level: float) -> ContainerStateView:
        container = self._containers.get(container_id)
        unit = container.level.unit
        target = Quantity(target_level, unit)

        events = container.fill(target)  # raises ExceedsMaxCapacity
        self._containers.save(container)

        for event in events:
            if isinstance(event, ContainerEmpty):
                self._alerts.on_container_empty(event)
            elif isinstance(event, ContainerLow):
                self._alerts.on_container_low(event)

        # Recover machine from ERROR when an operator fills a container
        if self._machine.state == MachineState.ERROR:
            self._machine.transition(MachineState.READY)
            self._display.show_ready()

        return ContainerStateView(
            container_id=container.id.value,
            level=container.level.value,
            unit=unit,
            max_capacity=container.max_capacity.value,
            low_threshold=container.low_threshold.value,
            state=container.state,
        )

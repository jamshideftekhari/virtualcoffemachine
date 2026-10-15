from __future__ import annotations

from domain.model.machine import CoffeeMachine
from domain.model.value_objects import MachineState

from application.ports.container_repository import ContainerRepository
from application.ports.display_port import DisplayPort
from application.use_cases.results import WasteStateView


class EmptyWaste:
    """
    Use case: an operator empties the waste container.

    Side effect: if the machine is in ERROR state (caused by a full waste container),
    emptying the waste transitions the machine back to READY.
    """

    def __init__(
        self,
        containers: ContainerRepository,
        machine: CoffeeMachine,
        display: DisplayPort,
    ) -> None:
        self._containers = containers
        self._machine = machine
        self._display = display

    def execute(self) -> WasteStateView:
        waste = self._containers.get_waste()
        waste.empty()
        self._containers.save_waste(waste)

        if self._machine.state == MachineState.ERROR:
            self._machine.transition(MachineState.READY)
            self._display.show_ready()

        return WasteStateView(
            brew_count=waste.brew_count,
            full_threshold=waste.full_threshold,
            state=waste.state,
        )

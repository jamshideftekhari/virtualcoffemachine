from __future__ import annotations

from domain.events import ContainerEmpty, ContainerLow, WasteContainerFull
from domain.exceptions import (
    InsufficientIngredient,
    MachineNotReady,
    RecipeNotFound,
    WasteContainerFullError,
)
from domain.model.brew_order import BrewOrder
from domain.model.machine import CoffeeMachine
from domain.model.value_objects import MachineState

from application.ports.alert_port import AlertPort
from application.ports.configuration_port import ConfigurationPort
from application.ports.container_repository import ContainerRepository
from application.use_cases.results import BrewResult


class BrewBeverage:
    """
    Use case: a customer selects a beverage and the machine brews it.

    Flow:
    1. Assert machine is READY
    2. Load recipe; check all ingredients (pre-brew, atomic)
    3. Check waste container is not full
    4. Transition machine → BREWING, start BrewOrder
    5. Deduct each ingredient; on mid-brew exhaustion → abort → ERROR
    6. Increment waste count
    7. Transition machine → READY, complete BrewOrder
    """

    def __init__(
        self,
        containers: ContainerRepository,
        config: ConfigurationPort,
        machine: CoffeeMachine,
        alerts: AlertPort,
    ) -> None:
        self._containers = containers
        self._config = config
        self._machine = machine
        self._alerts = alerts

    def execute(self, beverage_id: str) -> BrewResult:
        # --- Pre-flight checks (no state changes yet) ---
        self._machine.assert_ready()

        recipe = self._config.get_recipe(beverage_id)  # raises RecipeNotFound

        for req in recipe.requirements:
            container = self._containers.get(req.container_id)
            if not container.has_sufficient(req.amount):
                raise InsufficientIngredient(req.container_id, req.amount, container.level)

        waste = self._containers.get_waste()
        if waste.is_full():
            raise WasteContainerFullError(waste.brew_count, waste.full_threshold)

        # --- Start brew ---
        order = BrewOrder(beverage_id=beverage_id)
        self._machine.transition(MachineState.BREWING)
        order.start()

        # --- Deduct ingredients ---
        try:
            for req in recipe.requirements:
                container = self._containers.get(req.container_id)
                events = container.deduct(req.amount)
                self._containers.save(container)
                self._dispatch_container_events(events)
        except InsufficientIngredient as exc:
            # Defensive: mid-brew exhaustion (pre-check passed but race or bug)
            abort_event = order.abort("ingredient exhausted mid-brew", exc.container_id)
            self._machine.transition(MachineState.ERROR)
            self._alerts.on_brew_aborted(abort_event)
            raise

        # --- Accumulate waste ---
        waste_events = waste.increment()
        self._containers.save_waste(waste)
        for event in waste_events:
            if isinstance(event, WasteContainerFull):
                self._alerts.on_waste_full(event)

        # --- Complete ---
        complete_event = order.complete()
        self._machine.transition(MachineState.READY)

        return BrewResult(
            brew_order_id=order.id,
            beverage_id=beverage_id,
            status="completed",
        )

    def _dispatch_container_events(self, events: list) -> None:
        for event in events:
            if isinstance(event, ContainerEmpty):
                self._alerts.on_container_empty(event)
            elif isinstance(event, ContainerLow):
                self._alerts.on_container_low(event)

from __future__ import annotations

from domain.events import ContainerEmpty, ContainerLow, WasteContainerFull
from domain.exceptions import (
    DomainException,
    InsufficientIngredient,
    MachineNotReady,
    RecipeNotFound,
    WasteContainerFullError,
)
from domain.model.brew_order import BrewOrder
from domain.model.machine import CoffeeMachine
from domain.model.recipe import Recipe
from domain.model.value_objects import ContainerId, MachineState
from domain.model.waste_container import WasteContainer

from application.ports.alert_port import AlertPort
from application.ports.configuration_port import ConfigurationPort
from application.ports.container_repository import ContainerRepository
from application.ports.display_port import DisplayPort
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
        display: DisplayPort,
    ) -> None:
        self._containers = containers
        self._config = config
        self._machine = machine
        self._alerts = alerts
        self._display = display

    def execute(self, beverage_id: str) -> BrewResult:
        try:
            recipe, waste = self._preflight(beverage_id)
        except DomainException as exc:
            self._display.show_rejected(_rejection_message(exc))
            raise

        # --- Start brew ---
        order = BrewOrder(beverage_id=beverage_id)
        self._machine.transition(MachineState.BREWING)
        order.start()
        self._display.show_brewing(recipe.name)

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
            self._display.show_error(f"Out of {_container_label(exc.container_id)}")
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
        self._display.show_ready()

        return BrewResult(
            brew_order_id=order.id,
            beverage_id=beverage_id,
            status="completed",
        )

    def _preflight(self, beverage_id: str) -> tuple[Recipe, WasteContainer]:
        """Checks that must pass before any state changes. Raises a DomainException otherwise."""
        self._machine.assert_ready()

        recipe = self._config.get_recipe(beverage_id)  # raises RecipeNotFound

        for req in recipe.requirements:
            container = self._containers.get(req.container_id)
            if not container.has_sufficient(req.amount):
                raise InsufficientIngredient(req.container_id, req.amount, container.level)

        waste = self._containers.get_waste()
        if waste.is_full():
            raise WasteContainerFullError(waste.brew_count, waste.full_threshold)

        return recipe, waste

    def _dispatch_container_events(self, events: list) -> None:
        for event in events:
            if isinstance(event, ContainerEmpty):
                self._alerts.on_container_empty(event)
            elif isinstance(event, ContainerLow):
                self._alerts.on_container_low(event)


def _container_label(container_id: ContainerId) -> str:
    return container_id.value.replace("_", " ")


def _rejection_message(exc: DomainException) -> str:
    """Short text for the machine display explaining why an order was refused."""
    if isinstance(exc, InsufficientIngredient):
        return f"Refill {_container_label(exc.container_id)}"
    if isinstance(exc, WasteContainerFullError):
        return "Empty waste"
    if isinstance(exc, MachineNotReady):
        return "Not ready"
    if isinstance(exc, RecipeNotFound):
        return "Unknown drink"
    return "Error"

from __future__ import annotations

import logging

from domain.events import BrewAborted, ContainerEmpty, ContainerLow, WasteContainerFull

logger = logging.getLogger("coffee_machine.alerts")


class LogAlertAdapter:
    """
    Driven adapter — dispatches alerts as structured log messages.

    Swap this adapter to send alerts to a webhook, email, or monitoring
    system without touching the domain or application layers.
    """

    def on_container_low(self, event: ContainerLow) -> None:
        logger.warning(
            "CONTAINER LOW  container=%s  level=%s  threshold=%s",
            event.container_id.value,
            event.current_level,
            event.low_threshold,
        )

    def on_container_empty(self, event: ContainerEmpty) -> None:
        logger.error(
            "CONTAINER EMPTY  container=%s",
            event.container_id.value,
        )

    def on_waste_full(self, event: WasteContainerFull) -> None:
        logger.warning(
            "WASTE FULL  brew_count=%d  threshold=%d",
            event.brew_count,
            event.full_threshold,
        )

    def on_brew_aborted(self, event: BrewAborted) -> None:
        logger.error(
            "BREW ABORTED  brew_order_id=%s  beverage=%s  reason=%s  container=%s",
            event.brew_order_id,
            event.beverage_id,
            event.reason,
            event.container_id.value if event.container_id else "n/a",
        )

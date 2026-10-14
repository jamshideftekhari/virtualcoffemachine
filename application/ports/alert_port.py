from __future__ import annotations

from typing import Protocol

from domain.events import (
    BrewAborted,
    ContainerEmpty,
    ContainerLow,
    WasteContainerFull,
)


class AlertPort(Protocol):
    """
    Outbound port — notifies operators of conditions requiring attention.

    The prototype implementation logs to stdout.
    Future implementations may send to a webhook or monitoring system.
    """

    def on_container_low(self, event: ContainerLow) -> None: ...

    def on_container_empty(self, event: ContainerEmpty) -> None: ...

    def on_waste_full(self, event: WasteContainerFull) -> None: ...

    def on_brew_aborted(self, event: BrewAborted) -> None: ...

from __future__ import annotations

from typing import Protocol


class DisplayPort(Protocol):
    """
    Outbound port — shows the machine's status to the customer standing at it.

    Implementations must return immediately; any slow rendering happens elsewhere.

    The prototype ships two implementations:
    - LogDisplayAdapter       (logs what would be shown — for development)
    - SenseHatDisplayAdapter  (Raspberry Pi Sense HAT 8x8 LED matrix)
    """

    def show_ready(self) -> None:
        """Machine is waiting for an order."""
        ...

    def show_brewing(self, beverage_name: str) -> None:
        """A brew has started. Shown for a while, then the display returns to the machine state."""
        ...

    def show_error(self, message: str) -> None:
        """Machine entered ERROR. Shown until show_ready() is called."""
        ...

    def show_rejected(self, message: str) -> None:
        """An order was refused (e.g. 'Refill milk'). Shown briefly, then back to the machine state."""
        ...

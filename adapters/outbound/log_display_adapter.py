from __future__ import annotations

import logging

logger = logging.getLogger("coffee_machine.display")


class LogDisplayAdapter:
    """
    Driven adapter — logs what the display would show.

    Used when no Sense HAT is available (e.g. developing on a laptop).
    """

    def show_ready(self) -> None:
        logger.info("DISPLAY  ready  'Welcome'")

    def show_brewing(self, beverage_name: str) -> None:
        logger.info("DISPLAY  brewing  %r", beverage_name)

    def show_error(self, message: str) -> None:
        logger.info("DISPLAY  error  %r", message)

    def show_rejected(self, message: str) -> None:
        logger.info("DISPLAY  rejected  %r", message)

    def close(self) -> None:
        pass

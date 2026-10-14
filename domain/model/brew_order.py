from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from domain.events import BrewAborted, BrewCompleted, BrewStarted
from domain.model.value_objects import BrewStatus, ContainerId


@dataclass
class BrewOrder:
    """
    Aggregate root for a single beverage brew request.

    Tracks the lifecycle of one brew from creation to completion or abort.
    """

    beverage_id: str
    id: UUID = field(default_factory=uuid4)
    status: BrewStatus = field(default=BrewStatus.PENDING)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def start(self) -> BrewStarted:
        self._assert_status(BrewStatus.PENDING)
        self.status = BrewStatus.BREWING
        return BrewStarted(brew_order_id=self.id, beverage_id=self.beverage_id)

    def complete(self) -> BrewCompleted:
        self._assert_status(BrewStatus.BREWING)
        self.status = BrewStatus.COMPLETED
        return BrewCompleted(brew_order_id=self.id, beverage_id=self.beverage_id)

    def abort(
        self,
        reason: str,
        container_id: ContainerId | None = None,
    ) -> BrewAborted:
        self._assert_status(BrewStatus.BREWING)
        self.status = BrewStatus.ABORTED
        return BrewAborted(
            brew_order_id=self.id,
            beverage_id=self.beverage_id,
            reason=reason,
            container_id=container_id,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _assert_status(self, expected: BrewStatus) -> None:
        if self.status != expected:
            raise ValueError(
                f"Expected BrewOrder status {expected.value}, got {self.status.value}"
            )

from __future__ import annotations

from dataclasses import dataclass, field

from domain.events import MachineStateChanged
from domain.exceptions import InvalidStateTransition, MachineNotReady
from domain.model.value_objects import MachineState

# Valid (from_state, to_state) transitions
_VALID_TRANSITIONS: frozenset[tuple[MachineState, MachineState]] = frozenset(
    [
        (MachineState.IDLE, MachineState.READY),
        (MachineState.READY, MachineState.BREWING),
        (MachineState.READY, MachineState.IDLE),
        (MachineState.BREWING, MachineState.READY),
        (MachineState.BREWING, MachineState.ERROR),
        (MachineState.ERROR, MachineState.READY),
    ]
)


@dataclass
class CoffeeMachine:
    """
    Aggregate root for the machine's operational state.

    Enforces the state FSM — only valid transitions are allowed.
    """

    state: MachineState = field(default=MachineState.IDLE)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        return self.state == MachineState.READY

    def assert_ready(self) -> None:
        """Raise MachineNotReady if the machine is not in READY state."""
        if not self.is_ready():
            raise MachineNotReady(self.state)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def transition(self, to_state: MachineState) -> MachineStateChanged:
        """
        Move to a new state.

        Raises InvalidStateTransition if the move is not permitted.
        """
        if (self.state, to_state) not in _VALID_TRANSITIONS:
            raise InvalidStateTransition(self.state, to_state)

        event = MachineStateChanged(from_state=self.state, to_state=to_state)
        self.state = to_state
        return event

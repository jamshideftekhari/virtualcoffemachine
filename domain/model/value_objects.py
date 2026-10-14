from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContainerId(str, Enum):
    WATER = "water"
    COFFEE_A = "coffee_a"
    COFFEE_B = "coffee_b"
    MILK = "milk"
    CACAO = "cacao"


class ContainerState(str, Enum):
    EMPTY = "EMPTY"
    LOW = "LOW"
    NORMAL = "NORMAL"


class WasteState(str, Enum):
    EMPTY = "EMPTY"
    NORMAL = "NORMAL"
    FULL = "FULL"


class MachineState(str, Enum):
    IDLE = "IDLE"
    READY = "READY"
    BREWING = "BREWING"
    ERROR = "ERROR"


class BrewStatus(str, Enum):
    PENDING = "PENDING"
    BREWING = "BREWING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


@dataclass(frozen=True)
class Quantity:
    """Immutable value object representing an amount with a unit."""

    value: float
    unit: str

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"Quantity value cannot be negative: {self.value}")

    def __add__(self, other: Quantity) -> Quantity:
        self._assert_same_unit(other)
        return Quantity(self.value + other.value, self.unit)

    def __sub__(self, other: Quantity) -> Quantity:
        self._assert_same_unit(other)
        return Quantity(self.value - other.value, self.unit)

    def __lt__(self, other: Quantity) -> bool:
        self._assert_same_unit(other)
        return self.value < other.value

    def __le__(self, other: Quantity) -> bool:
        self._assert_same_unit(other)
        return self.value <= other.value

    def __gt__(self, other: Quantity) -> bool:
        self._assert_same_unit(other)
        return self.value > other.value

    def __ge__(self, other: Quantity) -> bool:
        self._assert_same_unit(other)
        return self.value >= other.value

    def __str__(self) -> str:
        return f"{self.value}{self.unit}"

    def _assert_same_unit(self, other: Quantity) -> None:
        if self.unit != other.unit:
            raise ValueError(f"Unit mismatch: {self.unit!r} vs {other.unit!r}")

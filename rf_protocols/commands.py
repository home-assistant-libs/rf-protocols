"""Common RF command definitions."""

import abc
from dataclasses import dataclass
from enum import StrEnum
from typing import override


class ModulationType(StrEnum):
    """RF modulation type."""

    OOK = "OOK"


@dataclass(frozen=True, slots=True)
class Timing:
    """High/low signal timing for OOK modulation."""

    high_us: int
    low_us: int


class RadioFrequencyCommand(abc.ABC):
    """Base class for RF commands."""

    frequency: int
    repeat_count: int
    modulation: ModulationType
    symbol_rate: int | None
    output_power: float | None

    def __init__(
        self,
        *,
        frequency: int,
        modulation: ModulationType,
        repeat_count: int = 0,
        symbol_rate: int | None = None,
        output_power: float | None = None,
    ) -> None:
        """Initialize the RF command."""
        self.frequency = frequency
        self.modulation = modulation
        self.repeat_count = repeat_count
        self.symbol_rate = symbol_rate
        self.output_power = output_power

    @abc.abstractmethod
    def get_raw_timings(self) -> list[Timing]:
        """Get raw timings for OOK commands."""


class OOKCommand(RadioFrequencyCommand):
    """OOK command with raw timings."""

    timings: list[Timing]

    def __init__(
        self,
        *,
        frequency: int,
        timings: list[Timing],
        repeat_count: int = 0,
        symbol_rate: int | None = None,
        output_power: float | None = None,
    ) -> None:
        """Initialize the OOK command."""
        super().__init__(
            frequency=frequency,
            modulation=ModulationType.OOK,
            repeat_count=repeat_count,
            symbol_rate=symbol_rate,
            output_power=output_power,
        )
        self.timings = timings

    @override
    def get_raw_timings(self) -> list[Timing]:
        """Get raw timings."""
        return self.timings

"""Common RF command definitions."""

from __future__ import annotations

import abc
from enum import StrEnum
from typing import override


class ModulationType(StrEnum):
    """RF modulation type."""

    OOK = "OOK"


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
    def get_raw_timings(self) -> list[int]:
        """Get raw timings as signed alternating microseconds.

        Even indices are pulse (high) durations expressed as positive
        microseconds; odd indices are space (low) durations expressed as
        negative microseconds. This matches Flipper's RAW ``.sub`` format.
        """

    def __repr__(self) -> str:
        """Return a concise representation for logging."""
        return (
            f"{type(self).__name__}("
            f"{self.modulation}, "
            f"{self.frequency / 1_000_000:g} MHz, "
            f"repeat={self.repeat_count})"
        )


class OOKCommand(RadioFrequencyCommand):
    """OOK command with raw timings."""

    timings: list[int]

    def __init__(
        self,
        *,
        frequency: int,
        timings: list[int],
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
    def get_raw_timings(self) -> list[int]:
        """Get raw timings."""
        return self.timings

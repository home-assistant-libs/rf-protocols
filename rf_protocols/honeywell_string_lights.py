"""Honeywell String Lights RF commands."""

from typing import override

from .commands import ModulationType, RadioFrequencyCommand, Timing

_FREQUENCY = 433_920_000
_REPEAT_COUNT = 50

_TURN_ON_TIMINGS = Timing.parse_timings(
    [
        2000,
        -550,
        1000,
        -550,
        450,
        -550,
        1000,
        -550,
        450,
        -550,
        1000,
        -550,
        450,
        -550,
        1000,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        1000,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
    ]
)

_TURN_OFF_TIMINGS = Timing.parse_timings(
    [
        2000,
        -550,
        1000,
        -550,
        450,
        -550,
        1000,
        -550,
        450,
        -550,
        1000,
        -550,
        450,
        -550,
        1000,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        450,
        -550,
        1000,
        -550,
    ]
)


class _HoneywellStringLightsCommand(RadioFrequencyCommand):
    """Base class for Honeywell String Lights commands."""

    def __init__(self) -> None:
        """Initialize a Honeywell String Lights command."""
        super().__init__(
            frequency=_FREQUENCY,
            modulation=ModulationType.OOK,
            repeat_count=_REPEAT_COUNT,
        )


class HoneywellStringLightsTurnOn(_HoneywellStringLightsCommand):
    """Honeywell String Lights turn on command."""

    @override
    def get_raw_timings(self) -> list[Timing]:
        """Return the raw timings for the turn on command."""
        return _TURN_ON_TIMINGS


class HoneywellStringLightsTurnOff(_HoneywellStringLightsCommand):
    """Honeywell String Lights turn off command."""

    @override
    def get_raw_timings(self) -> list[Timing]:
        """Return the raw timings for the turn off command."""
        return _TURN_OFF_TIMINGS

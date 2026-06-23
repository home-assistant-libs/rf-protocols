"""Encoder for Falmec cooker-hood RF remotes.

433.92 MHz OOK, biphase (each bit is a space+mark pair: ``1`` is a short
space then a long mark, ``0`` is a long space then a short mark).

Reverse-engineered from a Falmec hood remote with light, a 4-speed fan and
a 15-minute auto-off timer. Every frame carries the **full device state**:
light, fan speed and timer are independent bits and no checksum is present,
so any state can be composed directly rather than recorded as fixed button
codes. RFXCOM lists Falmec as a ``Fan`` subtype, which corroborates the
fixed-code (non-rolling) nature.

The frame is 16 biphase cells transmitted in order. Cells 6, 7 and 8 hold
the fan speed as a 3-bit value (0..4), cell 9 the light and cell 10 the
timer. The remaining cells form a per-remote address; the default matches
the unit this was decoded from. If your hood does not respond, capture your
own remote and adjust ``address``.
"""

from __future__ import annotations

from typing import override

from . import ModulationType, RadioFrequencyCommand

_DEFAULT_FREQUENCY = 433_920_000
_DEFAULT_REPEATS = 8
_DEFAULT_TIMEBASE_US = 320
_INTER_FRAME_US = 10_000

_FRAME_CELLS = 16
_FAN_BIT4_CELL = 6
_FAN_BIT2_CELL = 7
_FAN_BIT1_CELL = 8
_LIGHT_CELL = 9
_TIMER_CELL = 10

_MAX_FAN_SPEED = 4
# Address of the decoded remote: cells 0 and 13 set, all other non-state
# cells clear (cell index i maps to bit i of this value).
_DEFAULT_ADDRESS = 0x2001


class FalmecCookerHoodCommand(RadioFrequencyCommand):
    """Encode a Falmec cooker-hood RF remote frame.

    Carries the full target state. The hood acts on absolute state, so the
    fan can be set to any speed directly, including straight to off.
    """

    address: int
    light: bool
    fan_speed: int
    timer: bool
    timebase_us: int

    def __init__(
        self,
        *,
        light: bool,
        fan_speed: int,
        timer: bool,
        address: int = _DEFAULT_ADDRESS,
        timebase_us: int = _DEFAULT_TIMEBASE_US,
        frequency: int = _DEFAULT_FREQUENCY,
        repeat_count: int = _DEFAULT_REPEATS,
    ) -> None:
        """Initialize the Falmec command."""
        if fan_speed < 0 or fan_speed > _MAX_FAN_SPEED:
            raise ValueError("fan_speed must be in range 0..4")
        if address < 0 or address >= (1 << _FRAME_CELLS):
            raise ValueError(f"address must fit in {_FRAME_CELLS} bits")

        super().__init__(
            frequency=frequency,
            modulation=ModulationType.OOK,
            repeat_count=repeat_count,
        )
        self.address = address
        self.light = light
        self.fan_speed = fan_speed
        self.timer = timer
        self.timebase_us = timebase_us

    @override
    def get_raw_timings(self) -> list[int]:
        """Compute the frame timings as signed mark/space microseconds."""
        short_us = self.timebase_us
        long_us = 2 * short_us

        cells = [(self.address >> i) & 1 for i in range(_FRAME_CELLS)]
        cells[_FAN_BIT4_CELL] = (self.fan_speed >> 2) & 1
        cells[_FAN_BIT2_CELL] = (self.fan_speed >> 1) & 1
        cells[_FAN_BIT1_CELL] = self.fan_speed & 1
        cells[_LIGHT_CELL] = int(self.light)
        cells[_TIMER_CELL] = int(self.timer)

        timings: list[int] = [short_us]  # leading start mark
        for cell in cells:
            if cell:
                timings += [-short_us, long_us]
            else:
                timings += [-long_us, short_us]
        timings.append(-_INTER_FRAME_US)
        return timings

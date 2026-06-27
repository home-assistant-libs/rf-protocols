"""Encoder for Falmec cooker-hood RF remotes.

433.92 MHz OOK, biphase (each bit is a space+mark pair: ``1`` is a short
space then a long mark, ``0`` is a long space then a short mark).

Reverse-engineered from a Falmec hood remote with light, a 4-speed fan and a
15-minute auto-off timer. Every frame carries the full device state: light,
fan speed and timer are independent bits and no checksum is present, so any
state is composed directly rather than recorded as fixed button codes. RFXCOM
lists Falmec as a ``Fan`` subtype, which corroborates the fixed-code
(non-rolling) nature.

The frame is 16 biphase cells transmitted in order. Cells 6, 7 and 8 hold the
fan speed as a 3-bit value (0..4), cell 9 the light and cell 10 the timer; the
remaining cells are fixed framing observed on the decoded unit.
"""

from __future__ import annotations

from typing import override

from . import ModulationType, RadioFrequencyCommand

_FREQUENCY = 433_920_000
_REPEAT_COUNT = 8
# Biphase symbol durations measured on the remote (long is ~2x short).
_SHORT_US = 320
_LONG_US = 620
_INTER_FRAME_US = 10_000

_FRAME_CELLS = 16
_FAN_BIT4_CELL = 6
_FAN_BIT2_CELL = 7
_FAN_BIT1_CELL = 8
_LIGHT_CELL = 9
_TIMER_CELL = 10
_MAX_FAN_SPEED = 4
# Fixed framing bits of the decoded remote: cells 0 and 13 set (cell index i
# maps to bit i). A second unit may reveal a per-remote address here.
_FRAMING = 0x2001


class FalmecCookerHoodCommand(RadioFrequencyCommand):
    """Encode a Falmec cooker-hood RF remote frame.

    Carries the full target state. The hood acts on absolute state, so the fan
    can be set to any speed directly, including straight to off.
    """

    light: bool
    fan_speed: int
    timer: bool

    def __init__(self, *, light: bool, fan_speed: int, timer: bool) -> None:
        """Initialize the Falmec command."""
        if fan_speed < 0 or fan_speed > _MAX_FAN_SPEED:
            raise ValueError("fan_speed must be in range 0..4")

        super().__init__(
            frequency=_FREQUENCY,
            modulation=ModulationType.OOK,
            repeat_count=_REPEAT_COUNT,
        )
        self.light = light
        self.fan_speed = fan_speed
        self.timer = timer

    @override
    def get_raw_timings(self) -> list[int]:
        """Compute the frame timings as signed mark/space microseconds."""
        cells = [(_FRAMING >> i) & 1 for i in range(_FRAME_CELLS)]
        cells[_FAN_BIT4_CELL] = (self.fan_speed >> 2) & 1
        cells[_FAN_BIT2_CELL] = (self.fan_speed >> 1) & 1
        cells[_FAN_BIT1_CELL] = self.fan_speed & 1
        cells[_LIGHT_CELL] = int(self.light)
        cells[_TIMER_CELL] = int(self.timer)

        timings: list[int] = [_SHORT_US]  # leading start mark
        for cell in cells:
            if cell:
                timings += [-_SHORT_US, _LONG_US]
            else:
                timings += [-_LONG_US, _SHORT_US]
        timings.append(-_INTER_FRAME_US)
        return timings

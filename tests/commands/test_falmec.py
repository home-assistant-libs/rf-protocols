"""Tests for Falmec cooker-hood command encoding."""

import pytest

from rf_protocols import ModulationType, RadioFrequencyCommand
from rf_protocols.commands.falmec import FalmecCookerHoodCommand

_SHORT = 320
_LONG = 640
_GAP = 10_000


def _frame(set_cells: set[int]) -> list[int]:
    """Build the expected biphase frame from the set cell indices."""
    timings: list[int] = [_SHORT]
    for cell in range(16):
        if cell in set_cells:
            timings += [-_SHORT, _LONG]
        else:
            timings += [-_LONG, _SHORT]
    timings.append(-_GAP)
    return timings


def test_falmec_command_rf_parameters() -> None:
    """FalmecCookerHoodCommand stores expected RF command metadata."""
    cmd = FalmecCookerHoodCommand(light=False, fan_speed=0, timer=False)
    assert cmd.frequency == 433_920_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 8
    assert cmd.symbol_rate is None
    assert cmd.output_power is None


def test_falmec_command_is_radio_frequency_command() -> None:
    """FalmecCookerHoodCommand is a RadioFrequencyCommand subclass."""
    cmd = FalmecCookerHoodCommand(light=False, fan_speed=0, timer=False)
    assert isinstance(cmd, RadioFrequencyCommand)


@pytest.mark.parametrize("fan_speed", [-1, 5, 8])
def test_falmec_command_rejects_invalid_fan_speed(fan_speed: int) -> None:
    """fan_speed must be in range 0..4."""
    with pytest.raises(ValueError, match="fan_speed"):
        FalmecCookerHoodCommand(light=False, fan_speed=fan_speed, timer=False)


@pytest.mark.parametrize("address", [-1, 1 << 16])
def test_falmec_command_rejects_invalid_address(address: int) -> None:
    """address must fit in 16 bits."""
    with pytest.raises(ValueError, match="address"):
        FalmecCookerHoodCommand(
            light=False, fan_speed=0, timer=False, address=address
        )


def test_falmec_encodes_all_off() -> None:
    """Light off, fan off, timer off uses only the default address cells."""
    cmd = FalmecCookerHoodCommand(light=False, fan_speed=0, timer=False)
    assert cmd.get_raw_timings() == _frame({0, 13})


def test_falmec_encodes_light_only() -> None:
    """Light on adds cell 9, fan and timer stay clear."""
    cmd = FalmecCookerHoodCommand(light=True, fan_speed=0, timer=False)
    assert cmd.get_raw_timings() == _frame({0, 9, 13})


@pytest.mark.parametrize(
    ("fan_speed", "fan_cells"),
    [
        (0, set()),
        (1, {8}),
        (2, {7}),
        (3, {7, 8}),
        (4, {6}),
    ],
)
def test_falmec_encodes_fan_speed_as_binary(
    fan_speed: int, fan_cells: set[int]
) -> None:
    """Fan speed 0..4 is the 3-bit value across cells 6 (x4), 7 (x2), 8 (x1)."""
    cmd = FalmecCookerHoodCommand(light=False, fan_speed=fan_speed, timer=False)
    assert cmd.get_raw_timings() == _frame({0, 13} | fan_cells)


def test_falmec_encodes_timer_with_fan_running() -> None:
    """Timer on adds cell 10 on top of the running fan state."""
    cmd = FalmecCookerHoodCommand(light=False, fan_speed=4, timer=True)
    assert cmd.get_raw_timings() == _frame({0, 6, 10, 13})


def test_falmec_frame_has_fixed_length() -> None:
    """A frame is 1 start mark + 16 cells * 2 + 1 trailing gap = 34 timings."""
    cmd = FalmecCookerHoodCommand(light=True, fan_speed=3, timer=True)
    assert len(cmd.get_raw_timings()) == 34

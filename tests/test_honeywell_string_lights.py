"""Tests for Honeywell String Lights RF commands."""

from rf_protocols import (
    HoneywellStringLightsTurnOff,
    HoneywellStringLightsTurnOn,
    ModulationType,
    Timing,
)

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


def test_turn_on_radio_parameters() -> None:
    """Test HoneywellStringLightsTurnOn uses the expected radio parameters."""
    cmd = HoneywellStringLightsTurnOn()
    assert cmd.frequency == 433_920_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 50
    assert cmd.symbol_rate is None
    assert cmd.output_power is None


def test_turn_on_timings() -> None:
    """Test HoneywellStringLightsTurnOn returns the expected raw timings."""
    assert HoneywellStringLightsTurnOn().get_raw_timings() == _TURN_ON_TIMINGS


def test_turn_off_radio_parameters() -> None:
    """Test HoneywellStringLightsTurnOff uses the expected radio parameters."""
    cmd = HoneywellStringLightsTurnOff()
    assert cmd.frequency == 433_920_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 50
    assert cmd.symbol_rate is None
    assert cmd.output_power is None


def test_turn_off_timings() -> None:
    """Test HoneywellStringLightsTurnOff returns the expected raw timings."""
    assert HoneywellStringLightsTurnOff().get_raw_timings() == _TURN_OFF_TIMINGS


def test_turn_on_and_turn_off_differ() -> None:
    """Test the turn on and turn off commands encode different timings."""
    assert (
        HoneywellStringLightsTurnOn().get_raw_timings()
        != HoneywellStringLightsTurnOff().get_raw_timings()
    )

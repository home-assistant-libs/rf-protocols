"""Tests for the RF protocol definitions."""

import pytest

from rf_protocols import ModulationType, OOKCommand, RadioFrequencyCommand, Timing


def test_modulation_type_ook() -> None:
    """Test ModulationType enum has OOK value."""
    assert ModulationType.OOK == "OOK"
    assert ModulationType.OOK.value == "OOK"


def test_timing_frozen() -> None:
    """Test Timing is a frozen dataclass."""
    timing = Timing(high_us=350, low_us=1050)
    assert timing.high_us == 350
    assert timing.low_us == 1050


def test_timing_equality() -> None:
    """Test Timing equality comparison."""
    assert Timing(high_us=350, low_us=1050) == Timing(high_us=350, low_us=1050)
    assert Timing(high_us=350, low_us=1050) != Timing(high_us=350, low_us=350)


def test_timing_parse_timings() -> None:
    """Test Timing.parse_timings converts pulse/space ints to Timing pairs."""
    assert Timing.parse_timings([2000, -550, 450, -1000]) == [
        Timing(high_us=2000, low_us=550),
        Timing(high_us=450, low_us=1000),
    ]


def test_timing_parse_timings_empty() -> None:
    """Test Timing.parse_timings accepts an empty list."""
    assert Timing.parse_timings([]) == []


def test_timing_parse_timings_odd_length() -> None:
    """Test Timing.parse_timings rejects unpaired values."""
    with pytest.raises(ValueError):
        Timing.parse_timings([2000, -550, 450])


class _MockCommand(RadioFrequencyCommand):
    """Simple concrete command for testing the base class."""

    def __init__(
        self,
        *,
        frequency: int = 433_920_000,
        modulation: ModulationType = ModulationType.OOK,
        repeat_count: int = 0,
        symbol_rate: int | None = None,
        output_power: float | None = None,
    ) -> None:
        super().__init__(
            frequency=frequency,
            modulation=modulation,
            repeat_count=repeat_count,
            symbol_rate=symbol_rate,
            output_power=output_power,
        )

    def get_raw_timings(self) -> list[Timing]:
        """Return a simple test pattern."""
        return [Timing(high_us=350, low_us=1050), Timing(high_us=350, low_us=350)]


def test_command_defaults() -> None:
    """Test RadioFrequencyCommand default values."""
    cmd = _MockCommand()
    assert cmd.frequency == 433_920_000
    assert cmd.repeat_count == 0
    assert cmd.modulation == ModulationType.OOK
    assert cmd.symbol_rate is None
    assert cmd.output_power is None


def test_command_custom_values() -> None:
    """Test RadioFrequencyCommand with custom values."""
    cmd = _MockCommand(
        frequency=868_000_000,
        repeat_count=3,
        symbol_rate=4800,
        output_power=10.0,
    )
    assert cmd.frequency == 868_000_000
    assert cmd.repeat_count == 3
    assert cmd.modulation == ModulationType.OOK
    assert cmd.symbol_rate == 4800
    assert cmd.output_power == 10.0


def test_command_get_raw_timings() -> None:
    """Test get_raw_timings returns expected timings."""
    cmd = _MockCommand()
    timings = cmd.get_raw_timings()
    assert timings == [
        Timing(high_us=350, low_us=1050),
        Timing(high_us=350, low_us=350),
    ]


def test_ook_command() -> None:
    """Test OOKCommand with raw timings."""
    timings = [
        Timing(high_us=350, low_us=1050),
        Timing(high_us=350, low_us=350),
        Timing(high_us=350, low_us=0),
    ]
    cmd = OOKCommand(frequency=433_920_000, timings=timings)
    assert cmd.frequency == 433_920_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 0
    assert cmd.get_raw_timings() == timings


def test_ook_command_custom_values() -> None:
    """Test OOKCommand with custom radio parameters."""
    timings = [Timing(high_us=500, low_us=1000)]
    cmd = OOKCommand(
        frequency=868_000_000,
        timings=timings,
        repeat_count=2,
        symbol_rate=4800,
        output_power=10.0,
    )
    assert cmd.frequency == 868_000_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 2
    assert cmd.symbol_rate == 4800
    assert cmd.output_power == 10.0
    assert cmd.get_raw_timings() == timings

"""Tests for the RF protocol definitions."""

from rf_protocols import ModulationType, RadioFrequencyCommand, Timing


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

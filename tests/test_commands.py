"""Tests for the RF protocol definitions."""

from rf_protocols import ModulationType, OOKCommand, RadioFrequencyCommand


def test_modulation_type_ook() -> None:
    """Test ModulationType enum has OOK value."""
    assert ModulationType.OOK == "OOK"
    assert ModulationType.OOK.value == "OOK"


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

    def get_raw_timings(self) -> list[int]:
        """Return a simple test pattern."""
        return [350, -1050, 350, -350]


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
    assert cmd.get_raw_timings() == [350, -1050, 350, -350]


def test_ook_command() -> None:
    """Test OOKCommand with raw timings."""
    timings = [350, -1050, 350, -350]
    cmd = OOKCommand(frequency=433_920_000, timings=timings)
    assert cmd.frequency == 433_920_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 0
    assert cmd.get_raw_timings() == timings


def test_command_repr() -> None:
    """Test RadioFrequencyCommand has a readable repr for subclasses."""
    cmd = OOKCommand(
        frequency=433_920_000,
        timings=[350, -1050],
        repeat_count=5,
    )
    assert repr(cmd) == "OOKCommand(OOK, 433.92 MHz, repeat=5)"


def test_ook_command_custom_values() -> None:
    """Test OOKCommand with custom radio parameters."""
    timings = [500, -1000]
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

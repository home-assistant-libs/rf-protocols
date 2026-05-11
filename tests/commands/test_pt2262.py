"""Tests for PT2262 tristate command encoding."""

import pytest

from rf_protocols import ModulationType, RadioFrequencyCommand
from rf_protocols.commands.pt2262 import PT2262Command


def test_pt2262_command_rf_parameters() -> None:
    """PT2262Command stores expected RF command metadata."""
    cmd = PT2262Command(data="000000000FFF", timebase_us=275)
    assert cmd.frequency == 433_920_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 5
    assert cmd.symbol_rate is None
    assert cmd.output_power is None


def test_pt2262_command_is_radio_frequency_command() -> None:
    """PT2262Command is a RadioFrequencyCommand subclass."""
    cmd = PT2262Command(data="000000000FFF", timebase_us=275)
    assert isinstance(cmd, RadioFrequencyCommand)


def test_pt2262_command_normalizes_data_to_uppercase() -> None:
    """Lowercase tristate symbols are accepted and normalized."""
    cmd = PT2262Command(data="000000000fff", timebase_us=275)
    assert cmd.data == "000000000FFF"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ("0000", "exactly 12"),
        ("0000000000000", "exactly 12"),
        ("00000000000X", "only symbols"),
    ],
)
def test_pt2262_command_rejects_invalid_data(data: str, message: str) -> None:
    """Data must be exactly 12 tristate symbols from {0, 1, F}."""
    with pytest.raises(ValueError, match=message):
        PT2262Command(data=data, timebase_us=275)


def test_pt2262_command_encodes_expected_timings_for_all_zeroes() -> None:
    """12 zero symbols plus sync produce the expected pulse sequence."""
    cmd = PT2262Command(data="000000000000", timebase_us=100)
    short = 400
    long = 1200
    expected = ([short, -long, short, -long] * 12) + [short, -12_400]
    assert cmd.get_raw_timings() == expected


def test_pt2262_command_encodes_expected_timings_for_all_symbols() -> None:
    """Symbol encoding follows the protocol definition for 0, 1, and F."""
    cmd = PT2262Command(data="01F01F01F01F", timebase_us=100)
    short = 400
    long = 1200
    symbol_map = {
        "0": [short, -long, short, -long],
        "1": [long, -short, long, -short],
        "F": [short, -long, long, -short],
    }
    expected: list[int] = []
    for symbol in "01F01F01F01F":
        expected.extend(symbol_map[symbol])
    expected.extend([short, -12_400])
    assert cmd.get_raw_timings() == expected

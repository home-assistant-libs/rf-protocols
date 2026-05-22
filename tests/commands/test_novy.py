"""Tests for Novy cooker-hood command encoding."""

import pytest

from rf_protocols import ModulationType, RadioFrequencyCommand
from rf_protocols.commands.novy import NovyCookerHoodCommand


def test_novy_command_rf_parameters() -> None:
    """NovyCookerHoodCommand stores expected RF command metadata."""
    cmd = NovyCookerHoodCommand(channel=1, key="power")
    assert cmd.frequency == 433_920_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 5
    assert cmd.symbol_rate is None
    assert cmd.output_power is None


def test_novy_command_is_radio_frequency_command() -> None:
    """NovyCookerHoodCommand is a RadioFrequencyCommand subclass."""
    cmd = NovyCookerHoodCommand(channel=1, key="power")
    assert isinstance(cmd, RadioFrequencyCommand)


@pytest.mark.parametrize("channel", [0, 11, -1])
def test_novy_command_rejects_invalid_channel(channel: int) -> None:
    """Channel must be in range 1..10."""
    with pytest.raises(ValueError, match="channel"):
        NovyCookerHoodCommand(channel=channel, key="power")


def test_novy_command_rejects_invalid_key() -> None:
    """Unknown key names are rejected."""
    with pytest.raises(ValueError, match="key"):
        NovyCookerHoodCommand(channel=1, key="not_a_key")


def test_novy_command_encodes_channel_1_power() -> None:
    """Channel 1 + power produces the expected PWM frame."""
    cmd = NovyCookerHoodCommand(channel=1, key="power", timebase_us=360)
    short = 360
    long_ = 720
    bits = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0]
    expected: list[int] = [short]
    for bit in bits:
        expected += [-short, long_] if bit else [-long_, short]
    expected.append(-10_000)
    assert cmd.get_raw_timings() == expected


def test_novy_command_encodes_channel_1_plus_as_12_bit_frame() -> None:
    """Channel 1 + plus is a 12-bit frame (10-bit channel + 2-bit key)."""
    cmd = NovyCookerHoodCommand(channel=1, key="plus", timebase_us=360)
    timings = cmd.get_raw_timings()
    # 1 leading mark + 12 bits * 2 timings + 1 trailing gap = 26 timings.
    assert len(timings) == 26


def test_novy_command_encodes_channel_1_power_as_18_bit_frame() -> None:
    """Channel 1 + power is an 18-bit frame (10-bit channel + 8-bit key)."""
    cmd = NovyCookerHoodCommand(channel=1, key="power", timebase_us=360)
    timings = cmd.get_raw_timings()
    # 1 leading mark + 18 bits * 2 timings + 1 trailing gap = 38 timings.
    assert len(timings) == 38


@pytest.mark.parametrize("channel", range(1, 11))
def test_novy_command_encodes_every_channel(channel: int) -> None:
    """Every supported channel produces a valid 18-bit frame for power."""
    cmd = NovyCookerHoodCommand(channel=channel, key="power")
    timings = cmd.get_raw_timings()
    assert len(timings) == 38
    assert timings[-1] == -10_000


@pytest.mark.parametrize(
    ("key", "expected_bits"),
    [
        ("minus", 12),
        ("plus", 12),
        ("ambient", 12),
        ("power", 18),
        ("light", 18),
        ("light_minus", 18),
        ("light_plus", 18),
        ("ambient_minus", 18),
        ("ambient_plus", 18),
        ("minus_plus", 18),
    ],
)
def test_novy_command_frame_width_per_key(key: str, expected_bits: int) -> None:
    """Each key uses either a 12-bit or 18-bit frame per the spec."""
    cmd = NovyCookerHoodCommand(channel=1, key=key)
    timings = cmd.get_raw_timings()
    # 1 leading + 2 per bit + 1 trailing
    assert len(timings) == 2 + 2 * expected_bits

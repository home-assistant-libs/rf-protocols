"""Tests for KAKU PPM command encoding."""

import pytest

from rf_protocols import ModulationType, RadioFrequencyCommand
from rf_protocols.commands.kaku import KakuCommand


def test_kaku_command_rf_parameters() -> None:
    """KakuCommand stores expected RF command metadata."""
    cmd = KakuCommand(id=47113, group=False, channel=1, on=True, timebase_us=275)
    assert cmd.frequency == 433_920_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 4
    assert cmd.symbol_rate is None
    assert cmd.output_power is None


def test_kaku_command_is_radio_frequency_command() -> None:
    """KakuCommand is a RadioFrequencyCommand subclass."""
    cmd = KakuCommand(id=47113, group=False, channel=1, on=True, timebase_us=275)
    assert isinstance(cmd, RadioFrequencyCommand)


def test_kaku_command_stores_parameters() -> None:
    """Constructor parameters are stored on the command."""
    cmd = KakuCommand(id=123, group=True, channel=16, on=False)
    assert cmd.id == 123
    assert cmd.group is True
    assert cmd.channel == 16
    assert cmd.on is False
    assert cmd.dimlevel is None


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": -1, "group": False, "channel": 1, "on": True}, "id"),
        ({"id": 1 << 26, "group": False, "channel": 1, "on": True}, "id"),
        ({"id": 1, "group": False, "channel": 0, "on": True}, "channel"),
        ({"id": 1, "group": False, "channel": 17, "on": True}, "channel"),
        ({"id": 1, "group": False, "channel": 1}, "exactly one"),
        ({"id": 1, "group": False, "channel": 1, "on": True, "dimlevel": 50}, "exactly one"),
        ({"id": 1, "group": False, "channel": 1, "dimlevel": -1}, "dimlevel"),
        ({"id": 1, "group": False, "channel": 1, "dimlevel": 101}, "dimlevel"),
        ({"id": 1, "group": False, "on": True}, "channel"),
    ],
)
def test_kaku_command_rejects_invalid_parameters(
    kwargs: dict[str, object],
    message: str,
) -> None:
    """Constructor rejects invalid ranges and mode combinations."""
    with pytest.raises(ValueError, match=message):
        KakuCommand(**kwargs)  # pyright: ignore[reportArgumentType]


def test_kaku_command_on_off_frame_length() -> None:
    """On/off mode encodes 32 symbols: sync + 32 symbols + pause."""
    cmd = KakuCommand(id=47113, group=False, channel=1, on=True, timebase_us=100)
    timings = cmd.get_raw_timings()
    assert len(timings) == 2 + 32 * 4 + 2
    assert timings[:2] == [100, -1100]
    assert timings[-2:] == [100, -3900]


def test_kaku_command_dim_frame_length() -> None:
    """Dimming mode encodes 36 symbols: sync + 36 symbols + pause."""
    cmd = KakuCommand(id=47113, group=True, channel=16, dimlevel=60, timebase_us=100)
    timings = cmd.get_raw_timings()
    assert len(timings) == 2 + 36 * 4 + 2
    assert timings[:2] == [100, -1100]
    assert timings[-2:] == [100, -3900]


def test_kaku_command_dimlevel_affects_timings() -> None:
    """Different dim levels produce different encoded payload symbols."""
    base = {"id": 47113, "group": False, "channel": 2}
    low = KakuCommand(**base, dimlevel=20).get_raw_timings()
    high = KakuCommand(**base, dimlevel=80).get_raw_timings()
    assert low != high


def test_kaku_command_on_off_affects_timings() -> None:
    """On and off commands differ when all other parameters are equal."""
    base = {"id": 47113, "group": False, "channel": 2}
    on_timings = KakuCommand(**base, on=True).get_raw_timings()
    off_timings = KakuCommand(**base, on=False).get_raw_timings()
    assert on_timings != off_timings


def test_kaku_command_group_without_channel_defaults_to_channel_1() -> None:
    """When group=True and channel is omitted, channel defaults to 1."""
    cmd = KakuCommand(id=123, group=True, on=True)
    assert cmd.channel == 1


def test_kaku_command_group_without_channel_matches_explicit_channel_1() -> None:
    """Group command without channel produces same timings as channel=1."""
    implicit = KakuCommand(id=123, group=True, on=True).get_raw_timings()
    explicit = KakuCommand(id=123, group=True, channel=1, on=True).get_raw_timings()
    assert implicit == explicit

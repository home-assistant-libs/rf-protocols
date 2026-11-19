"""Tests for FS20 command encoding."""

import pytest

from rf_protocols import ModulationType, RadioFrequencyCommand
from rf_protocols.commands.fs20 import FS20Command, FS20CommandType


def _decode_frame(cmd: FS20Command) -> list[int]:
    """Decode raw timings back into frame bytes, validating the structure.

    Checks the preamble, start bit, pulse widths, per-byte even parity and
    the trailing stop bit, then returns the decoded frame bytes (including
    the checksum byte).
    """
    timebase = cmd.timebase_us
    timings = cmd.get_raw_timings()

    # Stop bit: one short mark followed by the inter-frame gap.
    assert timings[-2] == 2 * timebase
    assert timings[-1] == -10000

    bits = ""
    for high, low in zip(timings[0:-2:2], timings[1:-2:2], strict=True):
        if high == 2 * timebase and low == -2 * timebase:
            bits += "0"
        elif high == 3 * timebase and low == -3 * timebase:
            bits += "1"
        else:
            pytest.fail(f"unexpected pulse pair ({high}, {low})")

    assert bits[:12] == "0" * 12, "preamble must be 12 zero bits"
    assert bits[12] == "1", "start bit must be 1"

    payload = bits[13:]
    assert len(payload) % 9 == 0, "payload must be 9-bit groups (byte + parity)"

    data: list[int] = []
    for i in range(0, len(payload), 9):
        byte = int(payload[i : i + 8], 2)
        parity = int(payload[i + 8])
        assert parity == byte.bit_count() % 2, f"bad parity for byte {byte:#04x}"
        data.append(byte)
    return data


def test_fs20_command_rf_parameters() -> None:
    """FS20Command stores expected RF command metadata."""
    cmd = FS20Command(
        housecode="12341234",
        address="1234",
        command=FS20CommandType.ON_100_PERCENT,
    )
    assert cmd.frequency == 868_350_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 3
    assert cmd.symbol_rate is None
    assert cmd.output_power is None
    assert cmd.timebase_us == 200


def test_fs20_command_is_radio_frequency_command() -> None:
    """FS20Command is a RadioFrequencyCommand subclass."""
    cmd = FS20Command(housecode=0, address=0, command=FS20CommandType.OFF)
    assert isinstance(cmd, RadioFrequencyCommand)


def test_fs20_command_frame_length() -> None:
    """Standard frame: preamble + start + 5 bytes * 9 bits + stop bit."""
    cmd = FS20Command(
        housecode="12341234",
        address="1234",
        command=FS20CommandType.ON_100_PERCENT,
    )
    timings = cmd.get_raw_timings()
    assert len(timings) == (13 + 5 * 9) * 2 + 2


def test_fs20_command_frame_length_extended() -> None:
    """Extended frame carries one additional byte (9 more bits)."""
    cmd = FS20Command(
        housecode="12341234",
        address="1234",
        command=FS20CommandType.ON_TIMER,
        extension=53,
    )
    timings = cmd.get_raw_timings()
    assert len(timings) == (13 + 6 * 9) * 2 + 2


def test_fs20_command_known_frame() -> None:
    """A hand-computed reference frame is encoded correctly."""
    cmd = FS20Command(
        housecode=0x04D2,
        address=0x04,
        command=FS20CommandType.ON_TIMER,
    )
    # Checksum: (0x04 + 0xD2 + 0x04 + 0x19 + 0x06) & 0xFF == 0xF9
    assert _decode_frame(cmd) == [0x04, 0xD2, 0x04, 0x19, 0xF9]


def test_fs20_command_known_frame_extended() -> None:
    """An extended reference frame sets bit 5 and appends the extension byte."""
    cmd = FS20Command(
        housecode=0x04D2,
        address=0x04,
        command=FS20CommandType.OFF_TIMER,
        extension=0x10,
    )
    # Command byte: 0x18 | 0x20 == 0x38.
    # Checksum: (0x04 + 0xD2 + 0x04 + 0x38 + 0x10 + 0x06) & 0xFF == 0x28
    assert _decode_frame(cmd) == [0x04, 0xD2, 0x04, 0x38, 0x10, 0x28]


def test_fs20_command_attribute_keeps_enum_with_extension() -> None:
    """The command attribute stays the pure enum even when an extension is set."""
    cmd = FS20Command(
        housecode=0x04D2,
        address=0x04,
        command=FS20CommandType.OFF_TIMER,
        extension=0x10,
    )
    assert cmd.command is FS20CommandType.OFF_TIMER


def test_fs20_command_checksum_relation() -> None:
    """Last decoded byte equals sum of frame bytes + 6 modulo 256."""
    cmd = FS20Command(
        housecode="43214321",
        address="2413",
        command=FS20CommandType.TOGGLE_ON_OFF,
    )
    data = _decode_frame(cmd)
    assert data[-1] == (sum(data[:-1]) + 0x06) & 0xFF


def test_fs20_command_string_housecode_matches_int() -> None:
    """Quaternary string notation maps to the equivalent integer codes."""
    from_str = FS20Command(
        housecode="12341234",
        address="1234",
        command=FS20CommandType.OFF,
    )
    from_int = FS20Command(
        housecode=0x1B1B,
        address=0x1B,
        command=FS20CommandType.OFF,
    )
    assert from_str.housecode == 0x1B1B
    assert from_str.address == 0x1B
    assert from_str.get_raw_timings() == from_int.get_raw_timings()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"housecode": "12345678", "address": "1111"}, "housecode"),
        ({"housecode": "1234", "address": "1111"}, "housecode"),
        ({"housecode": -1, "address": "1111"}, "housecode"),
        ({"housecode": 1 << 16, "address": "1111"}, "housecode"),
        ({"housecode": "11111111", "address": "0123"}, "address"),
        ({"housecode": "11111111", "address": "123"}, "address"),
        ({"housecode": "11111111", "address": -1}, "address"),
        ({"housecode": "11111111", "address": 256}, "address"),
    ],
)
def test_fs20_command_rejects_invalid_parameters(
    kwargs: dict[str, object],
    message: str,
) -> None:
    """Constructor rejects invalid housecodes and addresses."""
    with pytest.raises(ValueError, match=message):
        FS20Command(command=FS20CommandType.OFF, **kwargs)  # pyright: ignore[reportArgumentType]


def test_fs20_command_rejects_wrong_type() -> None:
    """Constructor rejects housecodes that are neither string nor integer."""
    with pytest.raises(TypeError, match="housecode"):
        FS20Command(
            housecode=1.5,  # pyright: ignore[reportArgumentType]
            address="1111",
            command=FS20CommandType.OFF,
        )


def test_fs20_command_timebase_scales_timings() -> None:
    """All pulse widths except the final gap scale with the time base."""
    base = {
        "housecode": "12341234",
        "address": "1234",
        "command": FS20CommandType.ON_100_PERCENT,
    }
    slow = FS20Command(**base, timebase_us=200).get_raw_timings()
    fast = FS20Command(**base, timebase_us=100).get_raw_timings()
    assert len(slow) == len(fast)
    assert slow[:-1] == [2 * t for t in fast[:-1]]
    assert slow[-1] == fast[-1] == -10000


def test_fs20_command_timings_alternate_signs() -> None:
    """Timings strictly alternate between marks and spaces."""
    cmd = FS20Command(
        housecode="12341234",
        address="1234",
        command=FS20CommandType.DIM_UP,
    )
    timings = cmd.get_raw_timings()
    for i, timing in enumerate(timings):
        if i % 2 == 0:
            assert timing > 0, f"timings[{i}] should be positive (mark)"
        else:
            assert timing < 0, f"timings[{i}] should be negative (space)"


def test_fs20_command_timings_vary_by_command() -> None:
    """Different commands produce different timings."""
    base = {"housecode": "12341234", "address": "1234"}
    on = FS20Command(**base, command=FS20CommandType.ON_100_PERCENT)
    off = FS20Command(**base, command=FS20CommandType.OFF)
    assert on.get_raw_timings() != off.get_raw_timings()


def test_fs20_command_timings_vary_by_housecode() -> None:
    """Different housecodes produce different timings."""
    base = {"address": "1234", "command": FS20CommandType.OFF}
    a = FS20Command(**base, housecode="12341234")
    b = FS20Command(**base, housecode="43214321")
    assert a.get_raw_timings() != b.get_raw_timings()

"""Tests for the RF protocol definitions."""

from rf_protocols import ModulationType, RadioFrequencyCommand
from rf_protocols.commands.somfy_rts import SomfyRTSButton, SomfyRTSCommand


def test_somfy_rts_button_values() -> None:
    """Test SomfyRTSButton enum has expected protocol command values."""
    assert SomfyRTSButton.MY == 0x1
    assert SomfyRTSButton.UP == 0x2
    assert SomfyRTSButton.DOWN == 0x4
    assert SomfyRTSButton.PROG == 0x8


def test_somfy_rts_command_rf_parameters() -> None:
    """Test SomfyRTSCommand has correct hardcoded RF parameters."""
    cmd = SomfyRTSCommand(
        address=0x1A2B3C,
        rolling_code=42,
        button=SomfyRTSButton.UP,
    )
    assert cmd.frequency == 433_420_000
    assert cmd.modulation == ModulationType.OOK
    assert cmd.repeat_count == 2
    assert cmd.symbol_rate is None
    assert cmd.output_power is None


def test_somfy_rts_command_stores_parameters() -> None:
    """Test SomfyRTSCommand stores address, rolling_code, and button."""
    cmd = SomfyRTSCommand(
        address=0x1A2B3C,
        rolling_code=42,
        button=SomfyRTSButton.DOWN,
    )
    assert cmd.address == 0x1A2B3C
    assert cmd.rolling_code == 42
    assert cmd.button == SomfyRTSButton.DOWN


def test_somfy_rts_command_is_radio_frequency_command() -> None:
    """Test SomfyRTSCommand is a RadioFrequencyCommand."""
    cmd = SomfyRTSCommand(
        address=0x1A2B3C,
        rolling_code=1,
        button=SomfyRTSButton.PROG,
    )
    assert isinstance(cmd, RadioFrequencyCommand)


def test_somfy_rts_command_timings_alternate_signs() -> None:
    """Test that get_raw_timings returns strictly alternating positive/negative values."""
    cmd = SomfyRTSCommand(
        address=0x1A2B3C,
        rolling_code=1,
        button=SomfyRTSButton.UP,
    )
    timings = cmd.get_raw_timings()
    assert len(timings) > 0
    for i, t in enumerate(timings):
        assert t != 0
        if i % 2 == 0:
            assert t > 0, f"timings[{i}] should be positive (mark), got {t}"
        else:
            assert t < 0, f"timings[{i}] should be negative (space), got {t}"


def test_somfy_rts_command_timings_vary_by_button() -> None:
    """Test that different buttons produce different timings."""
    base = {"address": 0x1A2B3C, "rolling_code": 1}
    timings_up = SomfyRTSCommand(**base, button=SomfyRTSButton.UP).get_raw_timings()
    timings_down = SomfyRTSCommand(**base, button=SomfyRTSButton.DOWN).get_raw_timings()
    assert timings_up != timings_down


def test_somfy_rts_command_timings_vary_by_rolling_code() -> None:
    """Test that different rolling codes produce different timings."""
    base = {"address": 0x1A2B3C, "button": SomfyRTSButton.UP}
    timings_1 = SomfyRTSCommand(**base, rolling_code=1).get_raw_timings()
    timings_2 = SomfyRTSCommand(**base, rolling_code=2).get_raw_timings()
    assert timings_1 != timings_2


def test_somfy_rts_command_timings_vary_by_address() -> None:
    """Test that different addresses produce different timings."""
    base = {"rolling_code": 1, "button": SomfyRTSButton.UP}
    timings_a = SomfyRTSCommand(**base, address=0x1A2B3C).get_raw_timings()
    timings_b = SomfyRTSCommand(**base, address=0xABCDEF).get_raw_timings()
    assert timings_a != timings_b


def test_somfy_rts_command_frame_repeats() -> None:
    """Test that frame_repeats controls the number of 7-sync frames appended."""
    base = {"address": 0x1A2B3C, "rolling_code": 1, "button": SomfyRTSButton.UP}
    timings_3 = SomfyRTSCommand(**base, frame_repeats=3).get_raw_timings()
    timings_4 = SomfyRTSCommand(**base, frame_repeats=4).get_raw_timings()
    # More repeats → longer signal
    assert len(timings_4) > len(timings_3)

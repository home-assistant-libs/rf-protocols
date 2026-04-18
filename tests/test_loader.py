"""Tests for the .sub file loader."""

from pathlib import Path

import pytest

import rf_protocols
from rf_protocols import CodeCollection, ModulationType, OOKCommand, get_codes

_BUNDLED_CODES_ROOT = Path(rf_protocols.__file__).parent / "codes"
_BUNDLED_SUB_FILES = sorted(_BUNDLED_CODES_ROOT.rglob("*.sub"))

_SAMPLE_SUB = """\
Filetype: Flipper SubGhz RAW File
Version: 1
Frequency: 433920000
Preset: FuriHalSubGhzPresetOok650Async
Protocol: RAW
Repeat: 7
RAW_Data: 2000 -550 450 -1000
"""


def _write_sub(path: Path, content: str = _SAMPLE_SUB) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_bundled_sub_files_exist() -> None:
    """At least one bundled .sub file ships with the package."""
    assert _BUNDLED_SUB_FILES, f"No .sub files found under {_BUNDLED_CODES_ROOT}"


@pytest.mark.parametrize(
    "sub_file",
    _BUNDLED_SUB_FILES,
    ids=[str(p.relative_to(_BUNDLED_CODES_ROOT)) for p in _BUNDLED_SUB_FILES],
)
def test_bundled_sub_file_parses(sub_file: Path) -> None:
    """Every bundled .sub file parses into a valid OOK command."""
    device_dir = sub_file.parent.relative_to(_BUNDLED_CODES_ROOT)
    codes = get_codes(str(device_dir))
    cmd = codes.load_command(sub_file.stem.upper())
    assert isinstance(cmd, OOKCommand)
    assert cmd.frequency > 0
    assert cmd.modulation == ModulationType.OOK
    assert cmd.timings
    assert len(cmd.timings) % 2 == 0


def test_get_codes_bundled_honeywell() -> None:
    """Bundled Honeywell string lights codes can be discovered and loaded."""
    codes = get_codes("honeywell/string_lights")
    assert isinstance(codes, CodeCollection)
    cmd = codes.load_command("TURN_ON")
    assert isinstance(cmd, OOKCommand)
    assert cmd.frequency == 433_920_000
    assert cmd.repeat_count == 50
    assert cmd.timings[:2] == [2000, -550]


def test_load_command_caches_results(tmp_path: Path) -> None:
    """Repeated load_command calls return the same instance without re-reading."""
    sub_path = tmp_path / "vendor" / "device" / "power.sub"
    _write_sub(sub_path)
    codes = get_codes("vendor/device", base_dir=tmp_path)
    first = codes.load_command("POWER")
    sub_path.unlink()
    second = codes.load_command("POWER")
    assert first is second


def test_load_command_unknown_name(tmp_path: Path) -> None:
    """Requesting an unknown command name raises KeyError."""
    _write_sub(tmp_path / "vendor" / "device" / "power.sub")
    codes = get_codes("vendor/device", base_dir=tmp_path)
    with pytest.raises(KeyError, match="NOPE"):
        codes.load_command("NOPE")


def test_load_command_base_dir_override(tmp_path: Path) -> None:
    """Passing base_dir loads codes from an alternate location."""
    _write_sub(tmp_path / "vendor" / "device" / "power.sub")
    codes = get_codes("vendor/device", base_dir=tmp_path)
    cmd = codes.load_command("POWER")
    assert isinstance(cmd, OOKCommand)
    assert cmd.frequency == 433_920_000
    assert cmd.repeat_count == 7
    assert cmd.timings == [2000, -550, 450, -1000]


def test_load_command_base_dir_accepts_str(tmp_path: Path) -> None:
    """base_dir accepts a str as well as a Path."""
    _write_sub(tmp_path / "vendor" / "device" / "power.sub")
    codes = get_codes("vendor/device", base_dir=str(tmp_path))
    assert isinstance(codes.load_command("POWER"), OOKCommand)


def test_get_codes_missing_directory(tmp_path: Path) -> None:
    """get_codes raises FileNotFoundError when the directory is missing."""
    with pytest.raises(FileNotFoundError):
        get_codes("nope", base_dir=tmp_path)


def test_load_command_rejects_non_raw_protocol(tmp_path: Path) -> None:
    """Non-RAW protocols are rejected on load_command."""
    _write_sub(
        tmp_path / "vendor" / "device" / "power.sub",
        _SAMPLE_SUB.replace("Protocol: RAW", "Protocol: Princeton"),
    )
    codes = get_codes("vendor/device", base_dir=tmp_path)
    with pytest.raises(ValueError, match="Protocol"):
        codes.load_command("POWER")


def test_load_command_rejects_non_ook_preset(tmp_path: Path) -> None:
    """Non-OOK presets are rejected on load_command."""
    _write_sub(
        tmp_path / "vendor" / "device" / "power.sub",
        _SAMPLE_SUB.replace(
            "FuriHalSubGhzPresetOok650Async", "FuriHalSubGhzPreset2FSKDev238Async"
        ),
    )
    codes = get_codes("vendor/device", base_dir=tmp_path)
    with pytest.raises(ValueError, match="Preset"):
        codes.load_command("POWER")


def test_get_codes_rejects_path_escape(tmp_path: Path) -> None:
    """Paths that resolve outside of base_dir are rejected."""
    (tmp_path / "inside").mkdir()
    outside = tmp_path.parent / "outside_codes"
    outside.mkdir(exist_ok=True)
    _write_sub(outside / "power.sub")
    with pytest.raises(ValueError, match="outside"):
        get_codes("../outside_codes", base_dir=tmp_path / "inside")


def test_load_command_multiline_raw_data(tmp_path: Path) -> None:
    """Multiple RAW_Data lines are concatenated."""
    content = (
        "Filetype: Flipper SubGhz RAW File\n"
        "Version: 1\n"
        "Frequency: 433920000\n"
        "Preset: FuriHalSubGhzPresetOok650Async\n"
        "Protocol: RAW\n"
        "RAW_Data: 2000 -550\n"
        "RAW_Data: 450 -1000\n"
    )
    _write_sub(tmp_path / "vendor" / "device" / "power.sub", content)
    codes = get_codes("vendor/device", base_dir=tmp_path)
    cmd = codes.load_command("POWER")
    assert isinstance(cmd, OOKCommand)
    assert cmd.timings == [2000, -550, 450, -1000]
    assert cmd.repeat_count == 0


def test_load_command_rejects_odd_raw_data(tmp_path: Path) -> None:
    """Odd-length RAW_Data is rejected on load_command."""
    _write_sub(
        tmp_path / "vendor" / "device" / "power.sub",
        _SAMPLE_SUB.replace("2000 -550 450 -1000", "2000 -550 450"),
    )
    codes = get_codes("vendor/device", base_dir=tmp_path)
    with pytest.raises(ValueError, match="even number"):
        codes.load_command("POWER")

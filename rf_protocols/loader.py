"""Load RF command codes from Flipper ``.sub`` files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .commands import OOKCommand, RadioFrequencyCommand

_DEFAULT_BASE_DIR = Path(__file__).parent / "codes"


class CodeCollection:
    """A device's RF command codes on disk.

    Holds a resolved device directory. ``.sub`` files are not read until
    :meth:`load_command` is called.
    """

    def __init__(self, codes_dir: Path) -> None:
        """Store the resolved device directory."""
        self._codes_dir = codes_dir
        self._cache: dict[str, RadioFrequencyCommand] = {}

    def load_command(self, name: str) -> RadioFrequencyCommand:
        """Read and parse the ``.sub`` file for ``name``. Does I/O.

        Raises :class:`KeyError` if no command with that name exists.
        Cached per instance: subsequent calls with the same ``name`` return
        the previously-parsed command without re-reading the file.
        """
        if (cached := self._cache.get(name)) is not None:
            return cached
        sub_file = self._codes_dir / f"{name.lower()}.sub"
        if not sub_file.is_file():
            raise KeyError(f"No command {name!r} in {self._codes_dir}")
        cmd = _parse_sub_content(sub_file.read_text())
        self._cache[name] = cmd
        return cmd

    def __repr__(self) -> str:
        """Return a concise representation."""
        return f"CodeCollection({self._codes_dir})"


def load_codes(path: str, base_dir: Path | str | None = None) -> CodeCollection:
    """Return a :class:`CodeCollection` for a device.

    Resolves ``path`` under ``base_dir`` (default: bundled codes directory)
    and verifies the directory exists and stays within ``base_dir``. No
    ``.sub`` files are read.
    """
    root = (Path(base_dir) if base_dir is not None else _DEFAULT_BASE_DIR).resolve()
    codes_dir = (root / path).resolve()
    if not codes_dir.is_relative_to(root):
        raise ValueError(f"{path!r} resolves outside of {root}")
    if not codes_dir.is_dir():
        raise FileNotFoundError(f"No codes directory at {codes_dir}")
    return CodeCollection(codes_dir)


def _parse_sub_content(content: str) -> RadioFrequencyCommand:
    """Parse a Flipper ``.sub`` file into a :class:`RadioFrequencyCommand`."""
    fields: dict[str, str] = {}
    raw_parts: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if key == "RAW_Data":
            raw_parts.append(value)
        else:
            fields[key] = value

    protocol = fields.get("Protocol", "")
    if protocol != "RAW":
        raise ValueError(f"Unsupported Protocol {protocol!r}; only RAW is supported")

    preset = fields.get("Preset", "")
    if "Ook" not in preset:
        raise ValueError(
            f"Unsupported Preset {preset!r}; only OOK presets are supported"
        )

    if "Frequency" not in fields:
        raise ValueError("Missing Frequency field")
    if not raw_parts:
        raise ValueError("Missing RAW_Data field")

    timings = [int(v) for part in raw_parts for v in part.split()]
    if len(timings) % 2 != 0:
        raise ValueError("RAW_Data must contain an even number of values")

    kwargs: dict[str, Any] = {
        "frequency": int(fields["Frequency"]),
        "timings": timings,
        "repeat_count": int(fields.get("Repeat", "0")),
    }
    return OOKCommand(**kwargs)

"""Library to decode and encode radio frequency signals."""

from .commands import ModulationType, OOKCommand, RadioFrequencyCommand
from .loader import CodeCollection, load_codes

__all__ = [
    "CodeCollection",
    "ModulationType",
    "OOKCommand",
    "RadioFrequencyCommand",
    "load_codes",
]

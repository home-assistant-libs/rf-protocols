"""Novy cooker-hood RF codes."""

from rf_protocols.loader import CodeCollection, get_codes


def get_codes_for_code(code: int) -> CodeCollection:
    """Return the bundled `rf-protocols` collection for a Novy cooker-hood code."""
    return get_codes(f"novy/cooker_hood/code_{code}")

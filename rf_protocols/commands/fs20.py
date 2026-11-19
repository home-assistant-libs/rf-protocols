"""Encoder and protocol implementation for ELV FS20 wireless home automation system.

Protocol specification: 868.35 MHz, OOK/AM modulation, Manchester-like pulse
width modulation using quaternary symbols (1, 2, 3, 4).

Devices which use FS20 include:

- ELV FS20 ST (Switch actuators)
- ELV FS20 DI (Dimmer actuators)
- ELV FS20 RS (Roller shutter actuators)
- ELV FS20 FHT 80b (Heating controllers)
- ELV FS20 S4 / S20 (Wall transmitters and remote controls)

A standard FS20 command frame consists of:
- Preamble 12 bits (000000000000)
- Sync bit: 1 bit (1)
- Housecode high: 1 byte / 4 quaternary digits (values 1-4)
- Housecode low: 1 byte / 4 quaternary digits (values 1-4)
- Address: 1 byte / 4 quaternary digits (values 1-4) representing channel/key/group
- Command: 1 byte / 4 quaternary digits specifying the action (e.g., Off, On, Dim, Timer).
- Extension/Param: Optional 1 byte for extended commands (e.g., timer duration or dim level) if bit 5 is set in the Command byte.
- Checksum: 1 byte Sum of all frame bytes + 6 modulo 256.
- Stop bit

After every framebyte a parity bit (even) is inserted.

The physical layer uses variable pulse-width encoding based on a time base t
(typically a=200 µs):

              ____
    Bit 0 : _|    |____
             |<2a>|<2a>|
              ______
    Bit 1 : _|      |______
             |<-3a->|<-3a->|

References:
- https://www.fhemwiki.de/wiki/FS20_Allgemein
- https://www.seegel-systeme.de/2015/09/05/funksteckdosen-mit-dem-raspberry-pi-steuern
"""

from __future__ import annotations
from enum import IntEnum
from typing import override, Optional, Union

from . import ModulationType, RadioFrequencyCommand

_TIMEBASE = 200  # typical FS20 time base in microseconds

class FS20CommandType(IntEnum):
    OFF = 0
    ON_6_25_PERCENT = 1
    ON_12_5_PERCENT = 2
    ON_18_75_PERCENT = 3
    ON_25_PERCENT = 4
    ON_31_25_PERCENT = 5
    ON_37_5_PERCENT = 6
    ON_43_75_PERCENT = 7
    ON_50_PERCENT = 8
    ON_56_25_PERCENT = 9
    ON_62_5_PERCENT = 10
    ON_68_75_PERCENT = 11
    ON_75_PERCENT = 12
    ON_81_25_PERCENT = 13
    ON_87_5_PERCENT = 14
    ON_93_75_PERCENT = 15
    ON_100_PERCENT = 16
    ON_LAST_VALUE = 17
    TOGGLE_ON_OFF = 18
    DIM_UP = 19
    DIM_DOWN = 20
    DIM_UP_DOWN = 21
    SET_TIMER = 22
    STATUS_REQUEST = 23
    OFF_TIMER = 24
    ON_TIMER = 25
    LAST_VALUE_TIMER = 26
    RESET_TO_DEFAULT = 27
    UNUSED_1 = 28
    UNUSED_2 = 29
    UNUSED_3 = 30
    UNUSED_4 = 31

class FS20Command(RadioFrequencyCommand):
    """OOK command for FS20 devices"""

    timebase_us: int
    housecode: int
    address: int
    command: FS20CommandType
    extension: Optional[int]

    def __init__(
        self,
        *,
        housecode: Union[str, int], # 8 quaternary digits (1-4) or integer representing the house code
        address: Union[str, int], # 4 quaternary digits (1-4) or integer representing the address/channel/key/group
        command: FS20CommandType,
        extension: Optional[int] = None,
        frequency: int = 868_350_000,
        timebase_us: int = _TIMEBASE,
        repeat_count: int = 3,
    ) -> None:
        """Initialize the FS20 command from a housecode, address and command."""

        self.housecode = FS20Command._normalize_quaternary(housecode, 16, "housecode")
        self.address = FS20Command._normalize_quaternary(address, 8, "address")
        if extension is not None:
            if (extension < 0) or (extension > 255):
                raise ValueError("extension must be within 0..255")
        self.extension = extension
        self.command = command

        super().__init__(
            frequency=frequency,
            modulation=ModulationType.OOK,
            repeat_count=repeat_count,
        )
        self.timebase_us = timebase_us

    @staticmethod
    def _normalize_quaternary(value: Union[str, int], bits: int, name: str) -> int:
        if isinstance(value, str):
            expected_len = bits // 2
            if not set(value).issubset({"1", "2", "3", "4"}):
                raise ValueError(f"{name} must contain only symbols '1', '2', '3', and '4'")
            if len(value) != expected_len:
                raise ValueError(f"{name} must be exactly {expected_len} characters long")
            tmp = 0
            for i, digit in enumerate(value):
                tmp = tmp << 2
                tmp += int(digit) - 1
            return tmp
        elif isinstance(value, int):
            if value < 0 or value >= (1 << bits):
                raise ValueError(f"{name} must be between 0 and { (1 << bits) - 1 }")
            return value
        else:
            raise TypeError(f"{name} must be a string or integer")

    @override
    def get_raw_timings(self) -> list[int]:
        """Compute the FS20 frame timings followed after preamble & sync"""
        symbols = {
            "0": [2 * self.timebase_us, -2 * self.timebase_us],
            "1": [3 * self.timebase_us, -3 * self.timebase_us],
        }

        data: str = "0000000000001" # preamble + startbit
        ba = bytearray()
        ba.append(self.housecode >> 8)
        ba.append(self.housecode & 0xFF)
        ba.append(self.address)
        command_byte = self.command.value
        if self.extension is not None:
            command_byte |= 0x20 # extension bit
        ba.append(command_byte)
        if self.extension is not None:
            ba.append(self.extension)

        # calculate and append checksum
        cs: int = 0
        for b in ba:
            cs += b
        cs = (cs + 0x06) & 0xFF
        ba.append(cs)

        for byte in ba:
            data += f"{byte:08b}"
            data += "0" if (byte.bit_count() % 2 == 0) else "1" # even parity

        timings: list[int] = []
        for symbol in data:
            timings.extend(symbols[symbol])
        timings.extend([2 * self.timebase_us, -10000]) # stopbit

        return timings

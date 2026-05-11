"""Tests for EV1527 RF command encoding."""

import pytest

from rf_protocols import ModulationType, RadioFrequencyCommand
from rf_protocols.commands.ev1527 import EV1527Command


def test_ev1527_command_rf_parameters() -> None:
	"""EV1527Command stores expected RF command metadata."""
	cmd = EV1527Command(device_id=12345, data=0, timebase_us=275)
	assert cmd.frequency == 433_920_000
	assert cmd.modulation == ModulationType.OOK
	assert cmd.repeat_count == 4
	assert cmd.symbol_rate is None
	assert cmd.output_power is None


def test_ev1527_command_is_radio_frequency_command() -> None:
	"""EV1527Command is a RadioFrequencyCommand subclass."""
	cmd = EV1527Command(device_id=12345, data=0, timebase_us=275)
	assert isinstance(cmd, RadioFrequencyCommand)


def test_ev1527_command_stores_parameters() -> None:
	"""Constructor parameters are stored on the command."""
	cmd = EV1527Command(device_id=999, data=7)
	assert cmd.device_id == 999
	assert cmd.data == 7
	assert cmd.timebase_us == 275


@pytest.mark.parametrize(
	("kwargs", "message"),
	[
		({"device_id": -1, "data": 0}, "device_id"),
		({"device_id": 1 << 20, "data": 0}, "device_id"),
		({"device_id": 1, "data": -1}, "data"),
		({"device_id": 1, "data": 16}, "data"),
	],
)
def test_ev1527_command_rejects_invalid_parameters(
	kwargs: dict[str, object],
	message: str,
) -> None:
	"""Constructor rejects invalid ranges."""
	with pytest.raises(ValueError, match=message):
		EV1527Command(**kwargs)  # pyright: ignore[reportArgumentType]


def test_ev1527_command_frame_length() -> None:
	"""EV1527 encodes 24 symbols: sync + 24 bits."""
	cmd = EV1527Command(device_id=12345, data=0, timebase_us=100)
	timings = cmd.get_raw_timings()
	assert len(timings) == 2 + 24 * 2
	assert timings[:2] == [100, -3100]


def test_ev1527_command_bit_partition_is_20_id_plus_4_data_lsb() -> None:
	"""Payload is exactly 20 LSB-first device-id bits followed by 4 data bits."""
	cmd = EV1527Command(device_id=1, data=15, timebase_us=100)
	timings = cmd.get_raw_timings()
	pairs = [(timings[i], timings[i + 1]) for i in range(2, len(timings), 2)]
	bits = "".join("1" if high > abs(low) else "0" for high, low in pairs)

	assert len(bits) == 24
	assert len(bits[:20]) == 20
	assert len(bits[20:]) == 4
	assert bits[:20] == "10000000000000000000"
	assert bits[20:] == "1111"


def test_ev1527_command_data_affects_timings() -> None:
	"""Different data values produce different encoded payload symbols."""
	base = {"device_id": 12345}
	data_0 = EV1527Command(**base, data=0).get_raw_timings()
	data_15 = EV1527Command(**base, data=15).get_raw_timings()
	assert data_0 != data_15


def test_ev1527_command_device_id_affects_timings() -> None:
	"""Different device IDs produce different timings."""
	base = {"data": 5}
	id_1 = EV1527Command(**base, device_id=1).get_raw_timings()
	id_2 = EV1527Command(**base, device_id=2).get_raw_timings()
	assert id_1 != id_2

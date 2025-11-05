"""Test TSmart models."""

from aiotsmart.models import Mode, DiscoveredDevice, Configuration, Status


def test_mode_enum_values() -> None:
    """Test Mode enum values."""
    assert Mode.MANUAL == 0x00
    assert Mode.ECO == 0x01
    assert Mode.SMART == 0x02
    assert Mode.TIMER == 0x03
    assert Mode.TRAVEL == 0x04
    assert Mode.BOOST == 0x05
    assert Mode.LIMITED == 0x21
    assert Mode.CRITICAL == 0x22


def test_discovered_device() -> None:
    """Test DiscoveredDevice dataclass."""
    device = DiscoveredDevice(
        ip_address="192.168.1.100", device_id="ABC123", device_name="Test Device"
    )

    assert device.ip_address == "192.168.1.100"
    assert device.device_id == "ABC123"
    assert device.device_name == "Test Device"


def test_configuration() -> None:
    """Test Configuration dataclass."""
    config = Configuration(
        device_id="DEF456",
        device_name="Test Config",
        firmware_version="1.2.3",
        firmware_name="Test Firmware",
        raw_response=b"test_data",
    )

    assert config.device_id == "DEF456"
    assert config.device_name == "Test Config"
    assert config.firmware_version == "1.2.3"
    assert config.firmware_name == "Test Firmware"
    assert config.raw_response == b"test_data"


def test_status_no_errors() -> None:
    """Test Status dataclass with no errors."""
    status = Status(
        power=True,
        setpoint=22,
        mode=Mode.ECO,
        temperature_high=25,
        temperature_low=20,
        temperature_average=22,
        relay=False,
        error_e01=False,
        error_e02=False,
        error_e03=False,
        error_e04=False,
        error_e05=False,
        error_w01=False,
        error_w02=False,
        error_w03=False,
        raw_response=b"status_data",
    )

    assert status.power is True
    assert status.setpoint == 22
    assert status.mode == Mode.ECO
    assert status.temperature_high == 25
    assert status.temperature_low == 20
    assert status.temperature_average == 22
    assert status.relay is False
    assert status.has_error is False


def test_status_with_error_e01() -> None:
    """Test Status dataclass with error_e01."""
    status = Status(
        power=True,
        setpoint=22,
        mode=Mode.ECO,
        temperature_high=25,
        temperature_low=20,
        temperature_average=22,
        relay=False,
        error_e01=True,
        error_e02=False,
        error_e03=False,
        error_e04=False,
        error_e05=False,
        error_w01=False,
        error_w02=False,
        error_w03=False,
        raw_response=b"status_data",
    )

    assert status.has_error is True


def test_status_with_error_e02() -> None:
    """Test Status dataclass with error_e02."""
    status = Status(
        power=True,
        setpoint=22,
        mode=Mode.ECO,
        temperature_high=25,
        temperature_low=20,
        temperature_average=22,
        relay=False,
        error_e01=False,
        error_e02=True,
        error_e03=False,
        error_e04=False,
        error_e05=False,
        error_w01=False,
        error_w02=False,
        error_w03=False,
        raw_response=b"status_data",
    )

    assert status.has_error is True


def test_status_with_all_errors() -> None:
    """Test Status dataclass with all errors."""
    status = Status(
        power=True,
        setpoint=22,
        mode=Mode.ECO,
        temperature_high=25,
        temperature_low=20,
        temperature_average=22,
        relay=False,
        error_e01=True,
        error_e02=True,
        error_e03=True,
        error_e04=True,
        error_e05=True,
        error_w01=True,
        error_w02=True,
        error_w03=True,
        raw_response=b"status_data",
    )

    assert status.has_error is True

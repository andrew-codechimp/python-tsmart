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
    )

    assert config.device_id == "DEF456"
    assert config.device_name == "Test Config"
    assert config.firmware_version == "1.2.3"
    assert config.firmware_name == "Test Firmware"


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
        e01=False,
        e01_count=0,
        e02=False,
        e02_count=0,
        e03=False,
        e03_count=0,
        e04=False,
        e04_count=0,
        e05=False,
        e05_count=0,
        w01=False,
        w01_count=0,
        w02=False,
        w02_count=0,
        w03=False,
        w03_count=0,
    )

    assert status.power is True
    assert status.setpoint == 22
    assert status.mode == Mode.ECO
    assert status.temperature_high == 25
    assert status.temperature_low == 20
    assert status.temperature_average == 22
    assert status.relay is False

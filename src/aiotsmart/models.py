"""Models for TSmart."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Mode(IntEnum):
    """TSmart Modes."""

    MANUAL = 0x00
    ECO = 0x01
    SMART = 0x02
    TIMER = 0x03
    TRAVEL = 0x04
    BOOST = 0x05
    LIMITED = 0x21
    CRITICAL = 0x22


@dataclass
class DiscoveredDevice:
    """Discovery model."""

    ip_address: str
    device_id: str
    device_name: str


@dataclass
class Configuration:
    """Configuration model."""

    device_id: str
    device_name: str
    firmware_version: str
    firmware_name: str
    raw_response: bytes


@dataclass
class Status:
    """Status model."""

    power: bool
    setpoint: int
    mode: Mode
    temperature_high: int
    temperature_low: int
    temperature_average: int
    relay: bool
    error_e01: bool
    error_e02: bool
    error_e03: bool
    error_e04: bool
    error_e05: bool
    error_w01: bool
    error_w02: bool
    error_w03: bool
    raw_response: bytes

    @property
    def has_error(self) -> bool:
        """Is there any error."""
        return (
            self.error_e01
            or self.error_e02
            or self.error_e03
            or self.error_e04
            or self.error_e05
            or self.error_w01
            or self.error_w02
            or self.error_w03
        )

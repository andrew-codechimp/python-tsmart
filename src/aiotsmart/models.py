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
class Discovery:
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


@dataclass
class Status:
    """Status model."""

    power: str
    setpoint: str
    mode: str
    temperature_high: str
    temperature_low: str
    temperature_average: str
    relay: str

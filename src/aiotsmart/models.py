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


@dataclass(frozen=True, slots=True, kw_only=True)
class DiscoveredDevice:
    """Discovery model."""

    ip_address: str
    device_id: str
    device_name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Configuration:
    """Configuration model."""

    device_id: str
    device_name: str
    firmware_version: str
    firmware_name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Status:
    """Status model."""

    power: bool
    setpoint: int
    mode: Mode
    temperature_high: int
    temperature_low: int
    temperature_average: int
    relay: bool
    e01: bool
    e01_count: int
    e02: bool
    e02_count: int
    e03: bool
    e03_count: int
    e04: bool
    e04_count: int
    e05: bool
    e05_count: int
    w01: bool
    w01_count: int
    w02: bool
    w02_count: int
    w03: bool
    w03_count: int

"""Utility methods."""

from __future__ import annotations


def validate_checksum(data: bytes) -> bool:
    """Validate the checksum."""

    t = 0
    for b in data[:-1]:
        t = t ^ b
    return t ^ 0x55 == data[-1]


def add_checksum(data: bytes) -> bytearray:
    """Add a checksum."""

    t = 0
    request = bytearray(data)
    for b in request[:-1]:
        t = t ^ b
    request[-1] = t ^ 0x55

    return request

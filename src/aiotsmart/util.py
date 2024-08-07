"""Utility methods."""

from __future__ import annotations


def validate_checksum(data: bytes) -> bool:
    """Validate the checksum."""

    t = 0
    for b in data[:-1]:
        t = t ^ b
    return t ^ 0x55 == data[-1]

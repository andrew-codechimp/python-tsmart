"""Test utility functions."""

from aiotsmart.util import validate_checksum, add_checksum


def test_validate_checksum_valid():
    """Test validate_checksum with valid checksum."""
    # Test data with valid checksum
    data = b"\xf1\x00\x00\xa4"  # This should have a valid checksum
    assert validate_checksum(data) is True


def test_validate_checksum_invalid():
    """Test validate_checksum with invalid checksum."""
    # Test data with invalid checksum
    data = b"\xf1\x00\x00\xa5"  # This should have an invalid checksum
    assert validate_checksum(data) is False


def test_add_checksum():
    """Test add_checksum function."""
    # Test adding checksum to data
    data = b"\xf1\x00\x00\x00"
    result = add_checksum(data)
    
    # Verify result is bytearray
    assert isinstance(result, bytearray)
    
    # Verify checksum is valid
    assert validate_checksum(result) is True
    
    # Verify the checksum value
    assert result == bytearray(b"\xf1\x00\x00\xa4")


def test_add_checksum_different_data():
    """Test add_checksum with different data."""
    data = b"\x21\x00\x00\x00"
    result = add_checksum(data)
    
    assert isinstance(result, bytearray)
    assert validate_checksum(result) is True
    assert result == bytearray(b"\x21\x00\x00\x74")


def test_checksum_roundtrip():
    """Test that add_checksum and validate_checksum work together."""
    original_data = b"\xf2\x01\x02\x00"
    
    # Add checksum
    data_with_checksum = add_checksum(original_data)
    
    # Validate the checksum
    assert validate_checksum(data_with_checksum) is True
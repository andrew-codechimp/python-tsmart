"""Test TSmart exceptions."""

from aiotsmart.exceptions import (
    TSmartError,
    TSmartCancelledError,
    TSmartTimeoutError,
    TSmartBadResponseError,
)


def test_tsmart_error():
    """Test TSmart generic error."""
    error = TSmartError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_tsmart_cancelled_error():
    """Test TSmart cancelled error."""
    error = TSmartCancelledError("Operation cancelled")
    assert str(error) == "Operation cancelled"
    assert isinstance(error, TSmartError)


def test_tsmart_timeout_error():
    """Test TSmart timeout error."""
    error = TSmartTimeoutError("Operation timed out")
    assert str(error) == "Operation timed out"
    assert isinstance(error, TSmartError)


def test_tsmart_bad_response_error():
    """Test TSmart bad response error."""
    error = TSmartBadResponseError("Bad response received")
    assert str(error) == "Bad response received"
    assert isinstance(error, TSmartError)
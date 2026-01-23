"""Test TSmart exceptions."""

from aiotsmart.exceptions import (
    TSmartError,
    TSmartBadResponseError,
)


def test_tsmart_error() -> None:
    """Test TSmart generic error."""
    error = TSmartError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_tsmart_bad_response_error() -> None:
    """Test TSmart bad response error."""
    error = TSmartBadResponseError("Bad response received")
    assert str(error) == "Bad response received"
    assert isinstance(error, TSmartError)

"""Asynchronous Python client for TSmart."""


class TSmartError(Exception):
    """Generic exception."""


class TSmartConnectionError(TSmartError):
    """TSmart connection exception."""


class TSmartTimeoutError(TSmartError):
    """TSmart timeout exception."""


class TSmartValidationError(TSmartError):
    """TSmart validation exception."""


class TSmartNotFoundError(TSmartError):
    """TSmart not found exception."""


class TSmartNoResponseError(TSmartError):
    """TSmart no response exception."""

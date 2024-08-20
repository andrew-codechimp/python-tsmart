"""Asynchronous Python client for TSmart."""


class TSmartError(Exception):
    """Generic exception."""


class TSmartTimeoutError(TSmartError):
    """TSmart timeout exception."""


class TSmartBadResponseError(TSmartError):
    """TSmart bad response exception."""

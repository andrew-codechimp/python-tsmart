"""Asynchronous Python client for TSmart."""


class TSmartError(Exception):
    """Generic exception."""


class TSmartBadResponseError(TSmartError):
    """TSmart bad response exception."""

"""Asynchronous Python client for TSmart."""


class TSmartError(Exception):
    """Generic exception."""


class TSmartConnectionError(TSmartError):
    """TSmart connection exception."""


class TSmartValidationError(TSmartError):
    """TSmart validation exception."""


class TSmartNotFoundError(TSmartError):
    """TSmart not found exception."""


class TSmartBadRequestError(TSmartError):
    """TSmart bad request exception."""

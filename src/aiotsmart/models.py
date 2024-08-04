"""Models for TSmart."""

from __future__ import annotations
from typing import Optional

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class InfoResponse(DataClassORJSONMixin):
    """InfoResponse model."""

    services: Optional[list[Info]] = field(
        default=None, metadata=field_options(alias="info")
    )
    error: Optional[str] = None


@dataclass
class Info(DataClassORJSONMixin):
    """Info model."""

    service_id: str = field(metadata=field_options(alias="ID"))
    login: str
    postcode: str
    quota_monthly: str
    quota_remaining: str

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from oddstracker import __version__
from oddstracker.utils import get_utc_now


class HealthStatusResponse(BaseModel):
    status: Literal["running"] = Field(default="running")
    timestamp: datetime = Field(default_factory=get_utc_now)
    version: str | None = Field(default=__version__)
    startup_time: datetime | None = Field(default=None)

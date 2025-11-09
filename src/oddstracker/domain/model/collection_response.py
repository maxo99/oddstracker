from typing import Literal

from pydantic import BaseModel, Field

from oddstracker import __version__
from oddstracker.domain.providers import PROVIDER_KEYS_SUPPORTED


class CollectionResponse(BaseModel):
    status: Literal["queued", "success"] = Field(default="success")
    collected: int = Field(default=0)
    version: str | None = Field(default=__version__)
    provider_key: PROVIDER_KEYS_SUPPORTED | None = Field(default=None)

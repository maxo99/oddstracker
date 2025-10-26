import logging
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, String

from oddstracker.utils import get_utc_now

_names = ["h2h", "spreads", "totals"]

logger = logging.getLogger(__name__)



class Offer(BaseModel):
    event_id: str
    offer_type: str
    last_update: str
    bookmaker: str
    choice: str
    price: float
    point: float | None = None



class SportsEvent(BaseModel):
    id: str
# class SportsEvent(SQLModel, table=True):
#     id: str = Field(sa_column=Column(String, primary_key=True, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, default=get_utc_now),
        default_factory=get_utc_now,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=get_utc_now,
            onupdate=get_utc_now,
        ),
        default_factory=get_utc_now,
    )
    #
    sport_key: str
    sport_title: str
    commence_time: str
    home_team: str
    away_team: str
    offers: list[Offer]


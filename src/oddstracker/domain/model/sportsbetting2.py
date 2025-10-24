from datetime import datetime

from pydantic import BaseModel, model_validator
from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel

from oddstracker.utils import get_utc_now, sign_int


class OutcomeB(BaseModel):
    label: str
    changedDate: str
    odds: int
    oddsFractional: str
    oddsAmerican: str
    type: str
    status: str
    line: int | None = None

    @model_validator(mode="before")
    def clean_unwanted_fields(cls, kwargs):
        kwargs.pop("cashOutStatus", None)
        kwargs.pop("betOfferId", None)
        if _english_label := kwargs.pop("englishLabel", None):
            kwargs["label"] = _english_label
        return kwargs

    @property
    def oddsDecimal(self) -> float:
        return float(self.odds) / 1000

    @property
    def oddsLine(self) -> str | None:
        if self.type in ["handicap", "overunder"] and self.line is not None:
            return sign_int(str(int(self.line) // 1000))
        return None


class Outcome(BaseModel):
    name: str
    price: float
    point: float | None = None
    #
    # participant: str | None = None
    # participantId: int | None = None

    @property
    def displayTitle(self) -> str:
        return ""
        # match self.type.lower():
        #     case "match":
        #         return f"{self.participant} MoneyLine"
        #     case "handicap":
        #         return f"{self.participant} {self.oddsLine}"
        #     case "overunder":
        #         return f"{self.label} {self.oddsLine}"
        #     case _:
        #         raise ValueError(f"Unknown outcome type: {self.type}")

    @property
    def oddsData(self) -> dict:
        return {}
        # d = {
        #     "decimal": self.oddsDecimal,
        #     "fractional": self.oddsFractional,
        #     "american": sign_int(self.oddsAmerican),
        # }
        # if self.type in ["handicap", "overunder"]:
        #     d["points"] = self.oddsLine
        # return d


class Market(BaseModel):
    key: str
    last_update: str
    outcomes: list[Outcome]


class Bookmaker(BaseModel):
    key: str
    title: str
    last_update: str
    markets: list[Market]


class SportsEventInfo(BaseModel):
    id: str
    sport_key: str
    sport_title: str
    commence_time: str
    home_team: str
    away_team: str
    bookmakers: list[Bookmaker]

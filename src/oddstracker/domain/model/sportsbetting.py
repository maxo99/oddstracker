from datetime import datetime

from pydantic import BaseModel, model_validator
from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel

from oddstracker.utils import get_utc_now, sign_int

BET_OFFER_TYPES = ["match", "handicap", "overunder"]


class Outcome(BaseModel):
    name: str | None = None
    label: str
    changedDate: str
    odds: int
    oddsFractional: str
    oddsAmerican: str
    type: str
    line: int | None = None
    participant: str | None = None
    participantId: int | None = None
    status: str
    oddsData: dict | None = None

    @model_validator(mode="before")
    def clean_unwanted_fields(cls, kwargs):
        kwargs.pop("cashOutStatus", None)
        kwargs.pop("betOfferId", None)
        if _english_label := kwargs.pop("englishLabel", None):
            kwargs["label"] = _english_label
        return kwargs

    @model_validator(mode="after")
    def set_name(self) -> "Outcome":
        if self.name is not None:
            return self
        match self.type.lower():
            case "match":
                self.name = f"{self.participant} MoneyLine"
            case "handicap":
                self.name = f"{self.participant} {self.oddsLine}"
            case "overunder":
                self.name = f"{self.label} {self.oddsLine}"
            case _:
                raise ValueError(f"Unknown outcome type: {self.type}")
        return self

    def get_odds_data(self) -> dict:
        d = {
            "decimal": self.oddsDecimal,
            "fractional": self.oddsFractional,
            "american": sign_int(self.oddsAmerican),
        }
        if self.type in ["handicap", "overunder"]:
            d["points"] = self.oddsLine
        return d

    @property
    def oddsDecimal(self) -> float:
        return float(self.odds) / 1000

    @property
    def oddsLine(self) -> str | None:
        if self.type in ["handicap", "overunder"] and self.line is not None:
            return sign_int(str(int(self.line) // 1000))
        return None


class BetOffer(SQLModel, table=True):
    __tablename__ = "betoffer"  # type: ignore
    id: int = Field(sa_column=Column(BigInteger, primary_key=True, nullable=False))
    active: bool = Field(
        default=True, sa_column=Column(Boolean, nullable=False, default=True)
    )
    event_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("event.id"), index=True, nullable=False)
    )
    collected_at: datetime = Field(
        sa_column=Column(
            DateTime, primary_key=True, nullable=False, default=get_utc_now
        ),
        default_factory=get_utc_now,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            default=get_utc_now,
            onupdate=get_utc_now,
        ),
        default_factory=get_utc_now,
    )
    criterion: str
    type: str
    outcomes: list[dict] = Field(sa_column=Column(JSON))
    participants: dict = Field(default_factory=dict, sa_column=Column(JSON))

    @model_validator(mode="before")
    def build_betoffer(cls, kwargs):
        kwargs.pop("cashOutStatus", None)
        kwargs.pop("tags", None)
        kwargs.pop("sortOrder", None)
        # kwargs.pop("closed", None)
        if isinstance(kwargs.get("criterion", None), dict):
            _criterion = kwargs.pop("criterion")
            kwargs["criterion"] = _criterion["englishLabel"]

        if "eventId" in kwargs:
            kwargs["event_id"] = kwargs.pop("eventId")

        if isinstance(kwargs.get("betOfferType", None), dict):
            _bet_offer_type = (
                kwargs.pop("betOfferType")
                .get("englishName", "")
                .replace("/", "")
                .lower()
            )
            kwargs["type"] = _bet_offer_type
            outcomes = []
            for o in kwargs.get("outcomes", []):
                o["type"] = kwargs["type"]
                outcome = Outcome.model_validate(o)
                p = o.get("participant", None)
                if p:
                    if not kwargs.get("participants", None):
                        kwargs["participants"] = {}
                    kwargs["participants"].update({int(o.get("participantId", -1)): p})
                outcomes.append(
                    {**outcome.model_dump(), "oddsData": outcome.get_odds_data()}
                )
            kwargs["outcomes"] = outcomes
        return kwargs


class SportsEvent(SQLModel, table=True):
    __tablename__ = "event"  # type: ignore

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, default=get_utc_now),
        default_factory=get_utc_now,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            default=get_utc_now,
            onupdate=get_utc_now,
        ),
        default_factory=get_utc_now,
    )
    name: str
    # TODO add alias for englishName etc
    englishName: str
    homeName: str
    awayName: str
    start: str
    group: str
    state: str


class SportsBettingInfo:
    event: SportsEvent
    betOffers: list[BetOffer]

    def __init__(self, **data):
        try:
            _e = data.get("event", {})
            self.event = SportsEvent.model_validate(_e)
        except Exception as e:
            raise e
        try:
            _bo = []
            for bo in data.get("betOffers", []):
                try:
                    _bo.append(BetOffer.model_validate(bo))
                except Exception as e:
                    raise e
            self.betOffers = _bo
        except Exception as e:
            raise e

    @property
    def started(self) -> bool:
        return self.event.state.lower() == "started"

    @property
    def moneyLineOffer(self) -> BetOffer | None:
        for bo in self.betOffers:
            if bo.type == "match":
                return bo
        return None

    @property
    def pointSpreadOffer(self) -> BetOffer | None:
        for bo in self.betOffers:
            if bo.type == "handicap":
                return bo
        return None

    @property
    def overUnderOffer(self) -> BetOffer | None:
        for bo in self.betOffers:
            if bo.type == "overunder":
                return bo
        return None

    @property
    def participants(self) -> dict:
        if self.moneyLineOffer:
            return self.moneyLineOffer.participants
        return {"home": self.event.homeName, "away": self.event.awayName}

    @property
    def eventId(self) -> int:
        return self.event.id

    @property
    def eventName(self) -> str:
        return self.event.englishName

    def __str__(self) -> str:
        return f"KambiData({self.eventId=}, {self.eventName=}, {self.participants=}, betOffers={len(self.betOffers)})"

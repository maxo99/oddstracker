from datetime import UTC, datetime

from pydantic import BaseModel, field_serializer, field_validator, model_validator
from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel

# class Criterion(BaseModel):
#     id: int
#     label: str
#     englishLabel: str
#     order: list
#     occurrenceType: str
#     lifetime: str


# class BetOfferType(BaseModel):
#     id: int
#     name: str
#     englishName: str


# class Odds(BaseModel):
#     decimal: float
#     fractional: str
#     american: str


#     @field_validator("decimal", mode="before")
#     def validate_decimal(cls, v):
#         if isinstance(v, int) and v > 1000:
#             return v / 1000
#         return v
BET_OFFER_TYPES = ["match", "handicap", "over/under"]


def _get_utc_now():
    return datetime.now(UTC)


def sign_int(v) -> str:
    if isinstance(v, str) and not v.startswith("-"):
        if int(v) > 0:
            return f"+{v}"
        else:
            return str(v)
    return str(v)


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
        if "cashOutStatus" in kwargs:
            kwargs.pop("cashOutStatus")
        if "betOfferId" in kwargs:
            kwargs.pop("betOfferId")
        if "englishLabel" in kwargs:
            kwargs["label"] = kwargs.pop("englishLabel")
        return kwargs

    @field_validator("name", mode="after")
    def set_name(cls, v) -> str:
        if isinstance(v, str):
            return v
        match cls.type.lower():
            case "match":
                return f"{cls.participant} MoneyLine"
            case "handicap":
                return f"{cls.participant} {cls.oddsLine}"
            case "over/under":
                return f"{cls.label} {cls.oddsLine}"
            case _:
                raise ValueError(f"Unknown outcome type: {cls.type}")

    def get_odds_data(self) -> dict:
        d = {
            "decimal": self.oddsDecimal,
            "fractional": self.oddsFractional,
            "american": sign_int(self.oddsAmerican),
        }
        if self.type in ["handicap", "over/under"]:
            d["points"] = self.oddsLine
        return d

    @property
    def oddsDecimal(self) -> float:
        return float(self.odds) / 1000

    @property
    def oddsLine(self) -> str | None:
        if self.type in ["handicap", "over/under"] and self.line is not None:
            return sign_int(str(int(self.line) // 1000))
        return None


class BetOffer(SQLModel, table=True):
    __tablename__ = "betoffer"  # type: ignore
    id: int = Field(sa_column=Column(BigInteger, primary_key=True, nullable=False))
    collected_at: datetime = Field(
        sa_column=Column(
            DateTime, primary_key=True, nullable=False, default=_get_utc_now
        ),
        default_factory=_get_utc_now,
    )
    eventId: int = Field(
        sa_column=Column(BigInteger, ForeignKey("event.id"), index=True, nullable=False)
    )
    # closed: str
    # criterion: dict = Field(sa_column=Column(JSON))
    criterion: str
    betOfferType: str
    outcomes: list[dict] = Field(sa_column=Column(JSON))



    @model_validator(mode="before")
    def denormalize(cls, kwargs):
        kwargs.pop("cashOutStatus", None)
        kwargs.pop("tags", None)
        kwargs.pop("sortOrder", None)
        # kwargs.pop("closed", None)
        if isinstance(kwargs.get("criterion", None), dict):
            _criterion = kwargs.pop("criterion")
            kwargs["criterion"] = _criterion["englishLabel"]

        if isinstance(kwargs.get("betOfferType", None), dict):
            _bet_offer_type = kwargs.pop("betOfferType").get("englishName", "").lower()
            kwargs["betOfferType"] = _bet_offer_type
            outcomes = []
            for o in kwargs.get("outcomes", []):
                o["type"] = kwargs["betOfferType"]
                outcome = Outcome.model_validate(o)

                outcomes.append(
                    {
                        **outcome.model_dump(),
                        "oddsData": outcome.get_odds_data()
                    }
            )
            kwargs["outcomes"] = outcomes
        return kwargs






class KambiEvent(SQLModel, table=True):
    __tablename__ = "event"  # type: ignore

    # class SQLModelConfig:
    #     extra = "ignore"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, default=_get_utc_now),
        default_factory=_get_utc_now,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            default=_get_utc_now,
            onupdate=_get_utc_now,
        ),
        default_factory=_get_utc_now,
    )
    deleted_at: datetime | None = Field(
        sa_column=Column(DateTime, nullable=True, default=None), default=None
    )
    name: str
    englishName: str
    homeName: str
    awayName: str
    start: str
    group: str
    state: str


class KambiData:
    event: KambiEvent
    betOffers: list[BetOffer]

    def __init__(self, **data):
        try:
            _e = data.get("event", {})
            self.event = KambiEvent.model_validate(_e)
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
    def eventId(self) -> int:
        return self.event.id

    @property
    def eventName(self) -> str:
        return self.event.englishName

    def __str__(self) -> str:
        return f"KambiData(eventId={self.eventId}, eventName={self.eventName}, betOffers={len(self.betOffers)})"

from datetime import UTC, datetime

from pydantic import BaseModel, model_validator
from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel


class Criterion(BaseModel):
    id: int
    label: str
    englishLabel: str
    order: list
    occurrenceType: str
    lifetime: str


class BetOfferType(BaseModel):
    id: int
    name: str
    englishName: str


class Outcome(BaseModel):
    id: int
    label: str
    englishLabel: str
    odds: int
    line: int | None = None
    participant: str | None = None
    type: str
    betOfferId: int
    changedDate: str
    participantId: int | None = None
    oddsFractional: str
    oddsAmerican: str
    status: str

    @model_validator(mode="before")
    def validate_extra_fields(cls, values):
        if "cashOutStatus" in values:
            values.pop("cashOutStatus")
        return values


class BetOffer(SQLModel, table=True):
    __tablename__ = "betoffer"  # type: ignore
    id: int = Field(sa_column=Column(BigInteger, primary_key=True, nullable=False))
    collected_at: datetime = Field(
        sa_column=Column(
            DateTime, primary_key=True, nullable=False, default=datetime.now(UTC)
        )
    )
    eventId: int = Field(
        sa_column=Column(BigInteger, ForeignKey("event.id"), index=True, nullable=False)
    )
    # closed: str
    # criterion: dict = Field(sa_column=Column(JSON))
    # betOfferType: str = Field(sa_column=Column(JSON))
    criterion: str
    betOfferType: str
    outcomes: list[Outcome] = Field(sa_column=Column(JSON))

    @model_validator(mode="before")
    def denormalize(cls, values):
        if "cashOutStatus" in values:
            values.pop("cashOutStatus")
        if "tags" in values:
            values.pop("tags")
        if "sortOrder" in values:
            values.pop("sortOrder")
        if "closed" in values:
            values.pop("closed")

        if isinstance(values.get("betOfferType", None), dict):
            _bet_offer_type = values.pop("betOfferType")
            match _bet_offer_type.get("englishName", "").lower():
                case "handicap":
                    values["betOfferType"] = "Handicap"
                case "match":
                    values["betOfferType"] = "Match"
                case "over/under":
                    values["betOfferType"] = "Over/Under"
                case _:
                    raise ValueError(f"Unknown bet offer type: {_bet_offer_type}")
        if isinstance(values.get("criterion", None), dict):
            _criterion = values.pop("criterion")
            values["criterion"] = _criterion["englishLabel"]

        return values


class KambiEvent(SQLModel, table=True):
    __tablename__ = "event"  # type: ignore

    # class SQLModelConfig:
    #     extra = "ignore"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, default=datetime.now(UTC))
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            default=datetime.now(UTC),
            onupdate=datetime.now(UTC),
        )
    )
    deleted_at: datetime | None = Field(
        sa_column=Column(DateTime, nullable=True, default=None)
    )
    name: str
    englishName: str
    homeName: str
    awayName: str
    start: str
    group: str
    state: str


class KambiData(BaseModel):
    event: KambiEvent
    betOffers: list[BetOffer]

    @property
    def eventId(self) -> int:
        return self.event.id

    @property
    def eventName(self) -> str:
        return self.event.englishName

    def __repr__(self) -> str:
        return f"KambiData(eventId={self.eventId}, eventName={self.eventName}, betOffers={len(self.betOffers)})"

from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel

# class EventData(BaseModel):
#     id: int = Field(primary_key=True, nullable=False)
#     name: str
#     englishName: str
#     homeName: str
#     awayName: str
#     start: str
#     group: str
#     state: str
#     # nameDelimiter: str
#     # groupId: int
#     # path: List[PathItem]
#     # nonLiveBoCount: int
#     # sport: str
#     # tags: List[str]


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
    # cashOutStatus: str


class BetOffer(SQLModel, table=True):
    __tablename__ = "betoffer"  # type: ignore
    model_config = {"extra": "ignore"}

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, nullable=False))
    collected_at: datetime = Field(
        sa_column=Column(
            DateTime, primary_key=True, nullable=False, default=datetime.utcnow
        )
    )
    closed: str
    criterion: dict = Field(sa_column=Column(JSON))
    betOfferType: dict = Field(sa_column=Column(JSON))
    eventId: int = Field(
        sa_column=Column(BigInteger, ForeignKey("event.id"), index=True, nullable=False)
    )
    outcomes: list = Field(sa_column=Column(JSON))
    # tags: list[str]
    sortOrder: int
    # cashOutStatus: str


class KambiEvent(SQLModel, table=True):
    __tablename__ = "event"  # type: ignore
    model_config = {"extra": "ignore"}

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

    def __str__(self) -> str:
        return f"KambiData(eventId={self.eventId}, eventName={self.eventName}, betOffers={len(self.betOffers)})"
from typing import List
from pydantic import BaseModel
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


class BetOffer(SQLModel):
    class SQLModelConfig:
        extra = "ignore"
    id: int
    closed: str
    criterion: Criterion
    betOfferType: BetOfferType
    eventId: int
    outcomes: list[Outcome]
    # tags: list[str]
    sortOrder: int
    # cashOutStatus: str


class KambiEvent(SQLModel, table=True):
    class SQLModelConfig:
        extra = "ignore"

    # event: "EventData" = Field(...)
    # betOffers: List[BetOffer] = Field(default_factory=list)
    id: int = Field(primary_key=True, nullable=False)
    name: str
    englishName: str
    homeName: str
    awayName: str
    start: str
    group: str
    state: str

    def __init__(self, **data):
        try:
            data = {**data.pop("event"), **data}
            super().__init__(**data)
        except Exception as e:
            raise e

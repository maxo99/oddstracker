import logging

from pydantic import BaseModel

from oddstracker.domain.model.sportevent import EventOffer
from oddstracker.service import get_client

logger = logging.getLogger(__name__)


class OfferChange(BaseModel):
    bookmaker: str
    choice: str
    offer_type: str
    old_price: float
    new_price: float
    old_point: float | None
    new_point: float | None
    old_timestamp: str
    new_timestamp: str
    price_changed: bool
    point_changed: bool


class EventLineMovesResponse(BaseModel):
    event_id: str
    home_team: str
    away_team: str
    sport_title: str
    commence_time: str
    changes: list[OfferChange]


def _has_changed(current: EventOffer, previous: EventOffer) -> tuple[bool, bool]:
    """Returns (price_changed, point_changed)"""
    price_changed = abs(current.price - previous.price) > 0.001
    point_changed = False

    if current.point is not None and previous.point is not None:
        point_changed = abs(current.point - previous.point) > 0.001
    elif current.point != previous.point:
        point_changed = True

    return price_changed, point_changed


async def get_linemoves() -> list[EventLineMovesResponse]:
    logger.info("Fetching all bet offer changes across events")
    events = await get_client().get_events()

    changes_by_event = []

    for event in events:
        logger.info(f"Processing changes for event {event.id}")
        sporteventdata = await get_client().get_sporteventdata(
            event_id=event.id,
            offer_type="all",
            first_last=True,
        )
        if not sporteventdata:
            logger.info(f"No sport event data found for event {event.id}, skipping")
            continue

        unique_offers = sporteventdata.sort_uniqueoffers()
        event_changes = []

        for offer_key, offers in unique_offers.items():
            if len(offers) < 2:
                logger.debug(f"Offer {offer_key} has only {len(offers)} entry, skipping")
                continue

            offers_sorted = sorted(offers, key=lambda x: x.timestamp)
            current = offers_sorted[-1]
            previous = offers_sorted[-2]

            price_changed, point_changed = _has_changed(current, previous)

            if not price_changed and not point_changed:
                logger.debug(f"Offer {offer_key} has not changed")
                continue

            logger.info(
                f"Offer {offer_key} changed - price: {price_changed}, point: {point_changed}"
            )

            change = OfferChange(
                bookmaker=current.bookmaker,
                choice=current.choice,
                offer_type=current.offer_type,
                old_price=previous.price,
                new_price=current.price,
                old_point=previous.point,
                new_point=current.point,
                old_timestamp=previous.timestamp.isoformat(),
                new_timestamp=current.timestamp.isoformat(),
                price_changed=price_changed,
                point_changed=point_changed,
            )

            event_changes.append(change)

        if event_changes:
            response = EventLineMovesResponse(
                event_id=event.id,
                home_team=event.home_team,
                away_team=event.away_team,
                sport_title=event.sport_title,
                commence_time=event.commence_time,
                changes=event_changes,
            )
            changes_by_event.append(response)
            logger.info(f"Found {len(event_changes)} changes for event {event.id}")
        else:
            logger.debug(f"No changes found for event {event.id}")

    logger.info(f"Processed {len(events)} events, found changes in {len(changes_by_event)} events")
    return changes_by_event

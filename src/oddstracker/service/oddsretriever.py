from oddstracker.domain.model.sportevent import EventOffer, SportEvent
from oddstracker.service import get_client


async def get_sportevents() -> list[SportEvent]:
    return await get_client().get_events()


async def get_events():
    return await get_client().get_events()


async def get_sporteventdata(event_id: str, offer_type: str = "all"):
    return await get_client().get_sporteventdata(event_id, offer_type=offer_type)


async def get_sportevent_eventoffers(
    event_id: str,
    offer_type: str,
    range_query: bool = False,
) -> list[EventOffer]:
    return await get_client().get_eventoffers_for_sportevent(
        event_id,
        offer_type=offer_type,
        first_last=range_query,
    )

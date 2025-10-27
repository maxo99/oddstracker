from oddstracker.service import PG_CLIENT


async def get_events():
    return await PG_CLIENT.get_events()


async def get_event(event_id: str):
    return await PG_CLIENT.get_sporteventdata(event_id)


async def get_event_offer(event_id: int, offer: str):
    return await PG_CLIENT.get_eventoffers_for_sportevent(event_id, offer)


async def get_bet_offers(
    event_id: int,
    offer_type: str,
    range_query: bool = False,
):
    return await PG_CLIENT.get_eventoffers_for_sportevent(
        event_id,
        offer_type=offer_type,
        range_query=range_query,
    )

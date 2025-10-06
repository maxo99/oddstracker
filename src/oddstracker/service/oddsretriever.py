from oddstracker.service import PG_CLIENT


async def get_events():
    return await PG_CLIENT.get_events()


async def get_event(event_id: int):
    return await PG_CLIENT.get_event(event_id)


async def get_event_offer(event_id: int, offer: str):
    return await PG_CLIENT.get_bet_offers_for_event(event_id, offer)


async def get_bet_offers(event_id: int, range_query: bool = False):
    return await PG_CLIENT.get_bet_offers_for_event(event_id, range_query=range_query)

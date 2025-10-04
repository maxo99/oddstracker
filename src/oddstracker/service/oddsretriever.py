from oddstracker.service import PG_CLIENT


def get_events():
    return PG_CLIENT.get_events()


def get_event(event_id: int):
    return PG_CLIENT.get_event(event_id)


def get_bet_offers(event_id: int):
    return PG_CLIENT.get_bet_offers_for_event(event_id)

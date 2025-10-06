import logging

from oddstracker.domain.model.sportsbetting import SportsBettingInfo

logger = logging.getLogger(__name__)


def test_connection(postgres_client):
    try:
        postgres_client.validate_connection()
        print("Connection successful.")
    except Exception as e:
        print("PostgreSQL connection failed:", e)
        raise e


def test_event_store_retrieve(sample_events, postgres_client):
    TEST_LIMIT = 5
    sample_events = sample_events[:TEST_LIMIT]
    for i, e in enumerate(sample_events):
        logger.info(f"Adding event:{i} {e['event']['englishName']}")
        try:
            kdata = SportsBettingInfo(**e)
            postgres_client.add_event_and_betoffers(kdata.event, kdata.betOffers)
        except Exception as ex:
            logger.error(f"Failed to parse event: {e['event']['englishName']}")
            raise ex
    for i, e in enumerate(sample_events):
        logger.info(f"Retrieving event:{i} {e['event']['englishName']}")
        retrieved = postgres_client.get_event(e["event"]["id"])
        assert retrieved is not None
        betoffers = postgres_client.get_bet_offers_for_event(e["event"]["id"])
        assert len(betoffers) >= len(e.get("betOffers", []))
    assert True




# def test_get_bet_offers_for_event(sample_events, fix_postgresclient):
#     e = sample_events[0]
#     event = KambiEvent(**e["event"])
#     bet_offers = e.get("betOffers", [])
#     fix_postgresclient.add_event(event, bet_offers)
#     assert isinstance(event, KambiEvent)
#     assert event.be
#     for i, e in enumerate(sample_events):
#         logger.info(f"Parsing event:{i} {e['event']['englishName']}")
#         try:
#         except Exception as ex:
#             logger.error(f"Failed to parse event: {e['event']['englishName']}")
#             raise ex
#     assert True
#     logger.info(f"Parsed {len(sample_events)} events")
#     events = fix_postgresclient.get_events()
#     assert len(events) == len(sample_events)



from oddstracker.domain.kambi_event import KambiEvent
import logging

logger = logging.getLogger(__name__)

def test_one():
    pass


def test_kambi_event_loads(sample_events):
    for i, e in enumerate(sample_events):
        logger.info(f"Parsing event:{i} {e['event']['englishName']}")
        try:
            event = KambiEvent(**e)
            assert isinstance(event, KambiEvent)
        except Exception as ex:
            logger.error(f"Failed to parse event: {e['event']['englishName']}")
            raise ex
    assert True
    logger.info(f"Parsed {len(sample_events)} events")


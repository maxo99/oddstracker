import logging

from oddstracker.domain.kambi_event import BetOffer, KambiData, KambiEvent

logger = logging.getLogger(__name__)



def test_kambi_data_load(sample_events):
    for i, e in enumerate(sample_events):
        logger.info(f"Parsing event:{i} {e['event']['englishName']}")
        try:
            kdata = KambiData.model_validate(e)
            assert isinstance(kdata, KambiData)
            assert isinstance(kdata.event, KambiEvent)
            assert isinstance(kdata.betOffers, list)
            assert isinstance(kdata.betOffers[0], BetOffer)
            assert isinstance(kdata.betOffers[0].betOfferType, str)
        except Exception as ex:
            logger.error(f"Failed to parse event: {e['event']['englishName']}")
            raise ex
    assert True
    logger.info(f"Parsed {len(sample_events)} events")

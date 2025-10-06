import logging

import requests

from oddstracker.domain.model.sportsbetting import SportsBettingInfo
from oddstracker.domain.providers import PROVIDER
from oddstracker.service import PG_CLIENT

logger = logging.getLogger(__name__)


async def collect_and_store_kdata() -> dict:
    _bets_data = fetch_sports_betting_data()
    await store_sports_betting_info(_bets_data)
    return {"status": "collected", "events": len(_bets_data)}


def fetch_sports_betting_data() -> list[SportsBettingInfo]:
    try:
        resp = requests.get(PROVIDER.nfl_url, params=PROVIDER.qparams())
        data = resp.json()["events"]
        logger.info(f"Fetched {len(data)} events from {PROVIDER.sportsbook}")
    except Exception as ex:
        logger.error(f"Failed to fetch events from {PROVIDER.sportsbook} {ex}")
        raise ex
    out = []
    try:
        for e in data:
            kdata = SportsBettingInfo(**e)
            logger.debug(f"Collected: {kdata}")
            out.append(kdata)
    except Exception as ex:
        logger.error(f"Failed to parse KambiData: {ex}")
        raise ex
    return out


async def store_sports_betting_info(data: list[SportsBettingInfo]) -> None:
    logger.info(f"Storing {len(data)} events from {PROVIDER.sportsbook}")
    for kdata in data:
        try:
            logger.info(f"Processing event: {kdata}")
            await PG_CLIENT.add_event_and_betoffers(kdata.event, kdata.betOffers)
            logger.info(f"Stored: {kdata}")
        except Exception as ex:
            logger.error(ex)
    logger.info(f"Processed {len(data)} events from {PROVIDER.sportsbook}")

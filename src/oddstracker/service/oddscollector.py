import logging

import requests

from oddstracker.domain.kambi_event import KambiData
from oddstracker.domain.kambi_provider import PROVIDER
from oddstracker.service import PG_CLIENT

logger = logging.getLogger(__name__)


def collect_and_store_kdata() -> dict:
    _kdata = pull_kdata()
    store_kdata(_kdata)
    return {"status": "collected", "events": len(_kdata)}


def pull_kdata() -> list[KambiData]:
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
            kdata = KambiData(**e)
            logger.debug(f"Collected: {kdata}")
            out.append(kdata)
    except Exception as ex:
        logger.error(f"Failed to parse KambiData: {ex}")
        raise ex
    return out


def store_kdata(data: list[KambiData]) -> None:
    logger.info(f"Storing {len(data)} events from {PROVIDER.sportsbook}")
    for kdata in data:
        try:
            logger.info(f"Processing event: {kdata}")
            PG_CLIENT.add_event(kdata.event, kdata.betOffers)
            logger.info(f"Stored: {kdata}")
        except Exception as ex:
            logger.error(ex)
    logger.info(f"Processed {len(data)} events from {PROVIDER.sportsbook}")

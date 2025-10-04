import logging

import requests

from oddstracker.adapters.postgres_client import PostgresClient
from oddstracker.domain.kambi_event import KambiData
from oddstracker.domain.kambi_provider import PROVIDER

_postgres_client = PostgresClient()

logger = logging.getLogger(__name__)


def collect_kdata() -> list[KambiData]:
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
            _postgres_client.add_event(kdata.event, kdata.betOffers)
            logger.info(f"Stored: {kdata}")
        except Exception as ex:
            logger.error(ex)
    logger.info(f"Processed {len(data)} events from {PROVIDER.sportsbook}")

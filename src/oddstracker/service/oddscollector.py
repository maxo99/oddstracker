import logging

import requests

from oddstracker.adapters.postgres_client import PostgresClient
from oddstracker.domain.kambi_event import KambiData
from oddstracker.domain.kambi_provider import PROVIDER

_postgres_client = PostgresClient()

logger = logging.getLogger(__name__)


def collect_odds() -> int:
    try:
        resp = requests.get(PROVIDER.nfl_url, params=PROVIDER.qparams())
        data = resp.json()["events"]
        logger.info(f"Fetched {len(data)} events from {PROVIDER.sportsbook}")
    except Exception as ex:
        logger.error(f"Failed to fetch events from {PROVIDER.sportsbook} {ex}")
        return 0

    for e in data:
        try:
            logger.info(f"Processing event: {e['event']['id']}")
            kdata = KambiData(**e)
            _postgres_client.add_event(kdata.event, kdata.betOffers)
            logger.info(f"Stored: {kdata}")
        except Exception as ex:
            logger.error(ex)
    logger.info(f"Processed {len(data)} events from {PROVIDER.sportsbook}")
    return len(data)

import logging

import requests

from oddstracker.domain.model.converter import convert_to_sportsbetting_info
from oddstracker.domain.model.sportsbetting import (
    SportsBettingInfo,
)
from oddstracker.domain.providers import (
    KAMBI_PROVIDERS,
    KambiProvider,
    Provider,
    TheOddsAPIProvider,
)
from oddstracker.service import PG_CLIENT
from oddstracker.utils import store_json

logger = logging.getLogger(__name__)


async def collect_and_store_bettingdata(
    provider_key: str,
    league: str,
    db_store: bool = True,
) -> dict:
    provider = get_provider(provider_key)
    _raw_data = fetch_sports_betting_data(provider, league)
    store_json(f"{provider_key}_{league}", "raw", _raw_data)

    count = 0
    if db_store:
        _bets_data = convert_to_sportsbetting_info(provider_key, _raw_data)
        await store_sports_betting_info(_bets_data)
        count = len(_bets_data)

    return {"status": "collected", "events": count}


def fetch_sports_betting_data(provider: Provider, league: str) -> dict:
    try:
        logger.info(f"Fetching data from {provider}")
        resp = requests.get(provider.get_url(league), params=provider.qparams())
        if resp.status_code != 200:
            raise ValueError(
                f"Failed to fetch data from {provider}: {resp.status_code} {resp.text}"
            )
        if provider.provider_key == "theoddsapi":
            print("Usage for request", resp.headers["x-requests-last"])
            print("Remaining requests", resp.headers["x-requests-remaining"])
            print("Used requests", resp.headers["x-requests-used"])

        data = resp.json()
        logger.info(f"Fetched data from {provider}")
    except Exception as ex:
        logger.error(f"Failed to fetch events from {provider} {ex}")
        raise ex
    return data


async def store_sports_betting_info(data: list[SportsBettingInfo]) -> None:
    logger.info(f"Storing {len(data)} events to DB")
    for kdata in data:
        try:
            logger.info(f"Processing event: {kdata}")
            await PG_CLIENT.add_event_and_betoffers(kdata.event, kdata.betOffers)
            logger.info(f"Stored: {kdata}")
        except Exception as ex:
            logger.error(ex)
    logger.info(f"Processed {len(data)} events to DB")


def get_provider(provider_key: str) -> Provider:
    if provider_key == "kambi":
        return KambiProvider(**KAMBI_PROVIDERS[0])
    elif provider_key == "theoddsapi":
        return TheOddsAPIProvider()
    else:
        raise ValueError(f"Unsupported provider: {provider_key}")

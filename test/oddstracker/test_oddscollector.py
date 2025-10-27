import pytest

from oddstracker.service.oddscollector import collect_and_store_bettingdata


@pytest.mark.asyncio
@pytest.mark.skip(reason="Integration test that requires external API access")
async def test_odds_collector(postgres_client):
    # starting_count = len(await postgres_client.get_events())

    collected = await collect_and_store_bettingdata(
        provider_key="theoddsapi",
        league="nfl",
        db_store=False,
    )
    assert len(collected) > 0

    collected2 = await collect_and_store_bettingdata(
        provider_key="kambi",
        league="nfl",
        db_store=False,
    )
    assert len(collected2) > 0

    # assert len(events) > starting_count

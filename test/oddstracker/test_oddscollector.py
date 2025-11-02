import pytest

from oddstracker.service.oddscollector import collect_and_store_bettingdata


@pytest.mark.asyncio
async def test_odds_collector(
    mock_betting_data_requests,
):
    toa_result = await collect_and_store_bettingdata(
        provider_key="theoddsapi",
        league="nfl",
        db_store=True,
    )
    kambi_result = await collect_and_store_bettingdata(
        provider_key="kambi",
        league="nfl",
        db_store=True,
    )

    assert toa_result == {"status": "collected", "events": 0}
    assert kambi_result == {"status": "collected", "events": 0}
    assert mock_betting_data_requests.call_count == 2

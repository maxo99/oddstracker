import pytest


@pytest.mark.asyncio
async def test_odds_collector(
    postgres_client,
    mock_betting_data_requests,
):
    from oddstracker.service.oddscollector import collect_and_store_bettingdata

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

    assert toa_result["events"] >= 1
    assert kambi_result["events"] >= 1
    assert mock_betting_data_requests.call_count == 2

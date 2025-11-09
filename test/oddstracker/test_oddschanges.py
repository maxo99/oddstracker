import pytest

from oddstracker.service.oddschanges import get_linemoves


@pytest.mark.asyncio
async def test_oddschanges(
    postgres_client,
    mock_betting_data_requests,
):
    from oddstracker.service.oddscollector import collect_and_store_bettingdata

    await collect_and_store_bettingdata(
        provider_key="kambi",
        league="nfl",
        db_store=True,
    )

    changes = await get_linemoves()
    assert isinstance(changes, list)

    if len(changes) > 0:
        change = changes[0]
        assert hasattr(change, "event_id")
        assert hasattr(change, "home_team")
        assert hasattr(change, "away_team")
        assert hasattr(change, "changes")
        assert isinstance(change.changes, list)

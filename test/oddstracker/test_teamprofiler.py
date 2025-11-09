import pytest


@pytest.mark.asyncio
async def test_get_teams(
    postgres_client,
):
    from oddstracker.service.teamprofiler import get_teams

    teams = await get_teams()
    assert isinstance(teams, list)
    assert len(teams) == 32
    for team in teams:
        assert team.participant_id is not None
        assert team.participant_name is not None
        assert team.team_abbr is not None
        assert team.team_name is not None
        assert team.team_division is not None


@pytest.mark.asyncio
async def test_get_team_events(
    postgres_client,
    mock_betting_data_requests,
):
    from oddstracker.service.oddscollector import collect_and_store_bettingdata
    from oddstracker.service.teamprofiler import (
        get_events_by_teamabbr,
        get_team_by_abbr,
    )

    await collect_and_store_bettingdata(
        provider_key="kambi",
        league="nfl",
        db_store=True,
    )

    team_abbr = "MIA"
    events = await get_events_by_teamabbr(team_abbr)
    assert isinstance(events, list)
    assert len(events) >= 1
    _teamdata = await get_team_by_abbr(team_abbr)
    for event in events:
        assert _teamdata.team_abbr in (event.home_team, event.away_team)

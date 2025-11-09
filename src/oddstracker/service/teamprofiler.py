import nfl_data_py as nfl

from oddstracker.domain.model.sportevent import EventOffer, SportEvent
from oddstracker.domain.teamdata import NFL_DATA_PI_ABBR_TO_KAMBIDATA, TeamData
from oddstracker.service import get_client

TEAMS_CACHE = None


async def get_teams() -> list[TeamData]:
    global TEAMS_CACHE
    if not TEAMS_CACHE:
        await load_and_store_team_data()
        TEAMS_CACHE = await get_client().get_teams()
    return TEAMS_CACHE


async def load_and_store_team_data():
    teams = nfl.import_team_desc()
    _teams_data = [
        TeamData.from_nfl_data(row)
        for _, row in teams.iterrows()
        if row["team_abbr"] in NFL_DATA_PI_ABBR_TO_KAMBIDATA
    ]
    await get_client().add_teamdata(_teams_data)


async def get_team_by_abbr(team_abbr: str) -> TeamData:
    _teams = await get_teams()
    return list(filter(lambda t: t.team_abbr == team_abbr, _teams))[0]


async def get_events_by_teamabbr(team_abbr: str) -> list[SportEvent]:
    # team = await get_team_by_abbr(team_abbr)
    # if not team or not team.team_nick:
    #     raise ValueError(f"Team with abbreviation '{team_abbr}' not found.")
    return await get_client().get_events_by_teamabbr(team_abbr=team_abbr)


async def get_team_event_offers(team_abbr: str) -> list[EventOffer]:
    team = await get_team_by_abbr(team_abbr)
    if not team or not team.team_nick:
        raise ValueError(f"Team with abbreviation '{team_abbr}' not found.")
    event = (await get_client().get_events_by_teamabbr(team_abbr=team.team_abbr))[0]
    if not event:
        raise ValueError(f"No events found for team '{team_abbr}'.")
    return await get_client().get_eventoffers_for_sportevent(event_id=event.id)

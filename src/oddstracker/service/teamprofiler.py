
import nfl_data_py as nfl

from oddstracker.domain.teamdata import NFL_DATA_PI_ABBR_TO_KAMBIDATA, TeamData
from oddstracker.service import PG_CLIENT

TEAMS_CACHE = None


async def get_teams() -> list[TeamData]:
    global TEAMS_CACHE
    if not TEAMS_CACHE:
        await load_and_store_team_data()
        TEAMS_CACHE = await PG_CLIENT.get_teams()
    return TEAMS_CACHE


def load_team_data():
    teams = nfl.import_team_desc()
    return [
        TeamData.from_nfl_data(row)
        for _, row in teams.iterrows()
        if row["team_abbr"] in NFL_DATA_PI_ABBR_TO_KAMBIDATA
    ]


async def load_and_store_team_data():
    teams_data = load_team_data()
    await PG_CLIENT.add_teamdata(teams_data)


async def get_team_by_abbr(team_abbr: str) -> TeamData:
    _teams = await get_teams()
    return list(filter(lambda t: t.team_abbr == team_abbr, _teams))[0]


async def get_team_events(team_abbr: str):
    team = await get_team_by_abbr(team_abbr)
    if not team or not team.participant_name:
        raise ValueError(f"Team with abbreviation '{team_abbr}' not found.")
    return await PG_CLIENT.get_events_by_participant(team.participant_name)


async def get_team_event_offers(team_abbr: str):
    team = await get_team_by_abbr(team_abbr)
    if not team or not team.participant_name:
        raise ValueError(f"Team with abbreviation '{team_abbr}' not found.")
    event = (await PG_CLIENT.get_events_by_participant(team.participant_name))[0]
    if not event:
        raise ValueError(f"No events found for team '{team_abbr}'.")
    return await PG_CLIENT.get_bet_offers_for_event(event_id=event.id)

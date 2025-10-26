from oddstracker.service.oddscollector import convert_to_sportsbetting_info
from oddstracker.utils import store_json
from test.oddstracker.conftest import get_sample_events


def test_model_kambi():
    try:
        print("Testing load_json for provider: kambi")
        loaded_data = get_sample_events("kambi")
        assert loaded_data
        _bets_data = convert_to_sportsbetting_info("kambi", loaded_data)
        store_json("kambi", "worked", {"out": _bets_data})

        assert _bets_data
    except Exception as e:
        raise e


def test_model_theoddsapi():
    try:
        print("Testing load_json for provider: theoddsapi")
        loaded_data = get_sample_events("theoddsapi")
        assert loaded_data
        _bets_data = convert_to_sportsbetting_info("theoddsapi", loaded_data)
        store_json("theoddsapi", "worked", {"out": _bets_data})
        assert _bets_data
    except Exception as e:
        raise e

async def test_teams_loading():
    from oddstracker.service.teamprofiler import get_teams

    teams = await get_teams()
    assert isinstance(teams, list)
    assert len(teams) > 0
    for team in teams:
        assert team.participant_id is not None
        assert team.participant_name is not None
        assert team.team_abbr is not None
        assert team.team_name is not None
        assert team.team_division is not None

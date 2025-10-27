from oddstracker.service.oddscollector import convert_to_sportevents
from oddstracker.utils import store_json
from test.oddstracker.conftest import get_sample_events


def test_model_kambi():
    try:
        print("Testing load_json for provider: kambi")
        loaded_data = get_sample_events("kambi")
        assert loaded_data
        _bets_data = convert_to_sportevents("kambi", loaded_data)
        store_json("kambi", "worked", {"out": _bets_data})

        assert _bets_data
    except Exception as e:
        raise e


def test_model_theoddsapi():
    try:
        print("Testing load_json for provider: theoddsapi")
        loaded_data = get_sample_events("theoddsapi")
        assert loaded_data
        _bets_data = convert_to_sportevents("theoddsapi", loaded_data)
        store_json("theoddsapi", "worked", {"out": _bets_data})
        assert _bets_data
    except Exception as e:
        raise e


from oddstracker.service.oddscollector import pull_kdata


def test_odds_collector(fix_postgresclient):
    # starting_count = len(fix_postgresclient.get_events())

    collected  =  pull_kdata()
    assert len(collected) > 0
    # assert len(events) > starting_count

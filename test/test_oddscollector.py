from oddstracker.service.oddscollector import collect_kdata


def test_odds_collector(fix_postgresclient):
    # starting_count = len(fix_postgresclient.get_events())

    collected  =  collect_kdata()
    assert len(collected) > 0
    # assert len(events) > starting_count

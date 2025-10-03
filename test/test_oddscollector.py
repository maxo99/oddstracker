from oddstracker.service.oddscollector import collect_odds


def test_odds_collector(fix_postgresclient):
    # starting_count = len(fix_postgresclient.get_events())

    collected  =  collect_odds()
    assert collected > 0
    # assert len(events) > starting_count

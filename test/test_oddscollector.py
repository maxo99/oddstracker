from oddstracker.service.oddscollector import fetch_sports_betting_data


def test_odds_collector(postgres_client):
    # starting_count = len(postgres_client.get_events())

    collected  =  fetch_sports_betting_data()
    assert len(collected) > 0
    # assert len(events) > starting_count

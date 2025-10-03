from oddstracker.domain.kambi_event import KambiEvent


def test_one():
    pass


def test_kambi_event_loads(sample_events):
    for i, e in enumerate(sample_events):
        print(f"Parsing event:{i} {e['event']['englishName']}")
        try:
            event = KambiEvent(**e)
            assert isinstance(event, KambiEvent)
        except Exception as ex:
            print(f"Failed to parse event: {e['event']['englishName']}")
            raise ex
    assert True
    print(f"Parsed {len(sample_events)} events")

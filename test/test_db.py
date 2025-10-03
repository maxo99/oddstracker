import logging



logger = logging.getLogger(__name__)


def test_connection(fix_postgresclient):
    try:
        result = fix_postgresclient.validate_connection()
        print("Connection successful.")
    except Exception as e:
        # fix_postgresclient.client.info()
        print("PostgreSQL connection failed:", e)
        raise e

def test_event_store_retrieve(fix_postgresclient):
    try:
        event = fix_postgresclient.get_event(1)
        assert event.id == 1
        print("Event retrieval successful.")
    except Exception as e:
        print("Event retrieval failed:", e)
        raise e
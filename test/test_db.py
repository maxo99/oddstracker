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

from oddstracker.adapters.postgres_client import PostgresClient

PG_CLIENT: PostgresClient | None = None


def get_client() -> PostgresClient:
    global PG_CLIENT
    if PG_CLIENT is None:
        PG_CLIENT = PostgresClient()
    return PG_CLIENT

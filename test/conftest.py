from typing import Generator

import pytest

from oddstracker.adapters.postgres_client import PostgresClient


@pytest.fixture(scope="session")
def fix_postgresclient() -> Generator[PostgresClient, None, None]:
    _client = PostgresClient()
    yield _client
    _client.close()

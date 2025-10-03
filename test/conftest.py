import os
from typing import Generator
import json
from oddstracker.config import DATA_DIR
import pytest

from oddstracker.adapters.postgres_client import PostgresClient


@pytest.fixture(scope="session")
def fix_postgresclient() -> Generator[PostgresClient, None, None]:
    _client = PostgresClient()
    yield _client
    _client.close()


@pytest.fixture(scope="session")
def sample_events() -> list[dict]:
    path = os.path.join(DATA_DIR, "nfl-matches-events.json")
    with open(path) as f:
        data = json.load(f)
    return data["events"]

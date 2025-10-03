import json
import os
from collections.abc import Generator

import pytest

from oddstracker.adapters.postgres_client import PostgresClient
from oddstracker.config import DATA_DIR


@pytest.fixture(scope="session")
def fix_postgresclient() -> Generator[PostgresClient]:
    _client = PostgresClient()
    yield _client
    _client.close()


@pytest.fixture(scope="session")
def sample_events() -> list[dict]:
    path = os.path.join(DATA_DIR, "nfl-matches-events.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]

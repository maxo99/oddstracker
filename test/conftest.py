import json
import os
from collections.abc import Generator

import pytest
from sqlalchemy import text

from oddstracker.adapters.postgres_client import PostgresClient
from oddstracker.config import DATA_DIR

TEARDOWN = False


@pytest.fixture(scope="function")
def fix_postgresclient() -> Generator[PostgresClient]:
    _client = PostgresClient()
    yield _client
    if TEARDOWN:
        with _client.engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE betoffer, event CASCADE"))
            conn.commit()
    _client.close()


@pytest.fixture(scope="session")
def sample_events() -> list[dict]:
    path = os.path.join(DATA_DIR, "nfl-matches-events.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]

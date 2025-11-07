import json
import os
from collections.abc import AsyncGenerator, Generator
from functools import lru_cache
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

from oddstracker.adapters.postgres_client import PostgresClient
from oddstracker.config import DATA_DIR
from oddstracker.utils import load_json

TEARDOWN = False


# @pytest.fixture(scope="function")
# def fix_postgresclient() -> Generator[PostgresClient]:
#     _client = PostgresClient()
#     yield _client
#     if TEARDOWN:
#         with _client.engine.connect() as conn:
#             conn.execute(text("TRUNCATE TABLE betoffer, event CASCADE"))
#             conn.commit()
#     _client.close()


@lru_cache
def get_sample_events(provider_key: str) -> list[dict] | dict:
    return load_json(provider_key, "sample-raw")


class _MockResponse:

    def __init__(self, payload: Any, *, status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}
        self.text = json.dumps(payload)

    def json(self) -> Any:
        return self._payload


@pytest.fixture
def mock_betting_data_requests(mocker) -> Any:
    sample_payloads = {
        "kambi": get_sample_events("kambi"),
        "theoddsapi": get_sample_events("theoddsapi"),
    }

    def _get_response(provider_key: str, params: dict[str, Any]) -> Any:
        return sample_payloads[provider_key]

    def resolve_provider_key(url: str) -> str:
        if "kambicdn" in url:
            return "kambi"
        if "the-odds-api" in url or "theoddsapi" in url:
            return "theoddsapi"
        raise ValueError(f"Unsupported provider URL: {url}")

    def fake_requests_get(url: str, params: dict[str, Any] | None = None, **_: Any) -> _MockResponse:
        provider_key = resolve_provider_key(url)
        response_payload = _get_response(provider_key, params or {})
        headers: dict[str, str] = {}
        if provider_key == "theoddsapi":
            headers = {
                "x-requests-last": "0",
                "x-requests-remaining": "100",
                "x-requests-used": "0",
            }
        return _MockResponse(response_payload, headers=headers)

    return mocker.patch(
        "oddstracker.service.oddscollector.requests.get",
        side_effect=fake_requests_get,
    )


@pytest.fixture(scope="session")
def sample_events() -> list[dict]:
    path = os.path.join(DATA_DIR, "nfl-matches-events.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]


@pytest.fixture(scope="session")
def sample_raw() -> dict:
    return {k: load_json(k, "raw") for k in ["kambi", "theoddsapi"]}


class TimescaleContainer(PostgresContainer):

    def __init__(self, image: str = "timescale/timescaledb:latest-pg15", **kwargs):
        super().__init__(image=image, **kwargs)


@pytest.fixture(scope="session")
def postgres_container() -> Generator[TimescaleContainer]:
    with TimescaleContainer(
        image="timescale/timescaledb:latest-pg15",
        dbname="rotoreader_test",
        username="test_user",
        password="test_password",
        driver=None,
    ) as container:
        container.get_connection_url()
        yield container


@pytest.fixture(scope="session")
def db_config(postgres_container: TimescaleContainer) -> dict[str, Any]:
    """Database configuration from testcontainer."""
    sync_url = postgres_container.get_connection_url()
    async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    if not async_url.startswith("postgresql+asyncpg://"):
        async_url = sync_url.replace("postgresql://", "postgresql+asyncpg://")

    return {
        "host": postgres_container.get_container_host_ip(),
        "port": postgres_container.get_exposed_port(5432),
        "database": postgres_container.dbname,
        "username": postgres_container.username,
        "password": postgres_container.password,
        "url": async_url,
    }


@pytest_asyncio.fixture(scope="function")
async def postgres_client(
    db_config: dict[str, Any],
) -> AsyncGenerator[PostgresClient]:
    # Import and store original client
    import oddstracker.service

    original_client = oddstracker.service.PG_CLIENT

    client = None
    try:
        client = PostgresClient(db_url=db_config["url"], use_null_pool=True)

        async with client.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))

        await client.initialize()

        # Monkey patch the global PG_CLIENT
        oddstracker.service.PG_CLIENT = client

        yield client

    finally:
        # Restore original client
        oddstracker.service.PG_CLIENT = original_client
        if client:
            await client.close()

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
    return load_json(provider_key, "raw")


@pytest.fixture(scope="session")
def sample_events() -> list[dict]:
    path = os.path.join(DATA_DIR, "nfl-matches-events.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]


@pytest.fixture(scope="session")
def sample_raw() -> dict:
    return {k: load_json(k, "raw") for k in ["kambi", "theoddsapi"]}


class PgVectorContainer(PostgresContainer):
    """Custom PostgreSQL container with pgvector extension."""

    def __init__(self, image: str = "pgvector/pgvector:pg18", **kwargs):
        super().__init__(image=image, **kwargs)


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PgVectorContainer]:
    with PgVectorContainer(
        image="pgvector/pgvector:pg18",
        dbname="rotoreader_test",
        username="test_user",
        password="test_password",
        driver=None,  # Let asyncpg be used via the async engine
    ) as container:
        # Wait for container to be ready
        container.get_connection_url()
        yield container


@pytest.fixture(scope="session")
def db_config(postgres_container: PgVectorContainer) -> dict[str, Any]:
    """Database configuration from testcontainer."""
    # Get the sync URL and convert to async asyncpg URL
    sync_url = postgres_container.get_connection_url()
    # Replace psycopg2 driver with asyncpg for async operations
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
        # Create a new client for each test with the current event loop
        # Use NullPool to avoid connection pool issues across event loops in tests
        client = PostgresClient(db_url=db_config["url"], use_null_pool=True)

        # Setup: Create pgvector extension and initialize tables
        async with client.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))

        # Initialize tables
        await client.initialize()

        # Monkey patch the global PG_CLIENT
        oddstracker.service.PG_CLIENT = client

        yield client

    finally:
        # Restore original client
        oddstracker.service.PG_CLIENT = original_client
        if client:
            await client.close()

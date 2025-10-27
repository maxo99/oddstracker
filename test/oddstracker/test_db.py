import logging

import pytest

from oddstracker.domain.model.converter import convert_to_sportevents
from test.oddstracker.conftest import get_sample_events

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_connection(postgres_client):
    try:
        await postgres_client.validate_connection()
        print("Connection successful.")
    except Exception as e:
        print("PostgreSQL connection failed:", e)
        raise e


@pytest.mark.asyncio
async def test_teams_loading(postgres_client):
    from oddstracker.service.teamprofiler import get_teams

    teams = await get_teams()
    assert isinstance(teams, list)
    assert len(teams) > 0
    for team in teams:
        assert team.participant_id is not None
        assert team.participant_name is not None
        assert team.team_abbr is not None
        assert team.team_name is not None
        assert team.team_division is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_key", ["kambi", "theoddsapi"])
async def test_db_store_retrieve(provider_key, postgres_client):
    try:
        print(f"Testing load_json for provider: {provider_key}")
        loaded_data = get_sample_events(provider_key)
        assert loaded_data
        _sporteventdata = convert_to_sportevents(provider_key, loaded_data)[0]
        await postgres_client.add_sporteventdata(_sporteventdata)
        assert _sporteventdata

        retrieved = await postgres_client.get_sportevent(_sporteventdata.event.id)
        assert retrieved is not None
        event_offers = await postgres_client.get_eventoffers_for_sportevent(
            _sporteventdata.event.id
        )
        assert len(event_offers) >= len(_sporteventdata.offers)

    except Exception as e:
        raise e

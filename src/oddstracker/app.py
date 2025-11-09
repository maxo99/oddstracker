import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import __version__

from oddstracker import utils
from oddstracker.config import APP_PORT, LOG_LEVEL
from oddstracker.domain.model.collection_response import CollectionResponse
from oddstracker.domain.model.healthstatus import HealthStatusResponse
from oddstracker.domain.model.sportevent import EventOffer, SportEvent, SportEventData
from oddstracker.domain.providers import LEAGUES_SUPPORTED, PROVIDER_KEYS_SUPPORTED
from oddstracker.service import get_client
from oddstracker.service.oddschanges import EventLineMovesResponse, get_linemoves
from oddstracker.service.oddscollector import collect_and_store_bettingdata
from oddstracker.service.oddsretriever import (
    get_sportevent_eventoffers,
    get_sporteventdata,
    get_sportevents,
)
from oddstracker.service.teamprofiler import (
    get_events_by_teamabbr,
    get_team_by_abbr,
    get_team_event_offers,
    get_teams,
)
from oddstracker.utils import validate_betoffer_type

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    logging.info("FastApi lifespan starting.")
    # Startup
    await get_client().initialize()
    logging.info("PostgresClient initialized.")

    logging.info("Application startup complete.")
    yield
    logging.info("Application shutdown starting.")

    # Shutdown - cleanup if needed
    await get_client().close()
    logging.info("PostgresClient connection closed.")

    logging.info("Application shutdown complete.")


STARTUP = utils.get_utc_now()
logging.info(f"Application version:{__version__} startup time (UTC): {STARTUP}")
app = FastAPI(lifespan=lifespan)
add_pagination(app)

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
logging.info("Prometheus metrics instrumentation configured.")


@app.get("/")
def health():
    return HealthStatusResponse(startup_time=STARTUP)


@app.post("/collect")
async def collect_sportevents(
    provider_key: PROVIDER_KEYS_SUPPORTED = "kambi",
    league: LEAGUES_SUPPORTED = "nfl",
) -> CollectionResponse:
    return await collect_and_store_bettingdata(
        provider_key=provider_key,
        league=league,
    )


@app.get("/event", response_model_exclude_none=True)
async def sportevents() -> list[SportEvent]:
    return await get_sportevents()


@app.get("/event/{event_id}", response_model_exclude_none=True)
async def sportevent(event_id: str) -> SportEventData:
    result = await get_sporteventdata(event_id=event_id)
    if not result:
        raise ValueError(f"SportEvent with id '{event_id}' not found.")
    return result


@app.get("/event/{event_id}/offer/{offer_type}", response_model_exclude_none=True)
async def sportevent_get_eventoffers(
    event_id: str,
    offer_type: str,
    range: bool = False,
):
    return await get_sportevent_eventoffers(
        event_id,
        offer_type=validate_betoffer_type(offer_type),
        range_query=range,
    )


@app.get("/team", response_model_exclude_none=True)
async def teams():
    return await get_teams()


@app.get("/team/{team_abbr}/events", response_model_exclude_none=True)
async def team_events(team_abbr: str):
    return await get_events_by_teamabbr(team_abbr)


@app.get("/team/{team_abbr}/offers", response_model_exclude_none=True)
async def team_event_offers(team_abbr: str) -> list[EventOffer]:
    team = await get_team_by_abbr(team_abbr)
    if not team or not team.team_nick:
        raise ValueError(f"Team with abbreviation '{team_abbr}' not found.")
    return await get_team_event_offers(team_abbr)


@app.get("/linemoves", response_model_exclude_none=True)
async def linemoves() -> list[EventLineMovesResponse]:
    return await get_linemoves()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_level=LOG_LEVEL)

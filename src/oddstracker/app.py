import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import __version__

from oddstracker import utils
from oddstracker.app_initializer import instrument_prometheus, instrument_tracing, setup_tracing
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
    logging.info(f"Application startup starting with app:{app.version}.")


    await get_client().initialize()
    logging.info("PostgresClient initialized.")
    logging.info("Application startup complete.")
    yield

    logging.info("Application shutdown starting.")
    await get_client().close()
    logging.info("Application shutdown complete.")


START_UP = utils.get_utc_now()
logger.info(f"Application version:{__version__} startup time (UTC): {START_UP}")

setup_tracing()
app = FastAPI(
    lifespan=lifespan,
    version=__version__,
)
add_pagination(app)
instrument_tracing(app)
instrument_prometheus(app)



instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
logging.info("Prometheus metrics instrumentation configured.")


@app.get("/", operation_id="health_check", tags=["Health"])
def health():
    return HealthStatusResponse(startup_time=START_UP)


@app.put(
    "/collect",
    summary="Collect SportEvents and BettingData",
    response_model_exclude_none=True,
    tags=["DataCollection", "SportEvents"],
    operation_id="collect_sportevents",
)
async def collect_sportevents(
    provider_key: PROVIDER_KEYS_SUPPORTED = "kambi",
    league: LEAGUES_SUPPORTED = "nfl",
) -> CollectionResponse:
    return await collect_and_store_bettingdata(
        provider_key=provider_key,
        league=league,
    )


@app.get(
    "/event",
    response_model_exclude_none=True,
    tags=["SportEvents"],
    operation_id="get_sportevents",
)
async def sportevents() -> list[SportEvent]:
    return await get_sportevents()


@app.get(
    "/event/{event_id}",
    response_model_exclude_none=True,
    tags=["SportEvents"],
    operation_id="get_sportevent_by_event_id",
)
async def sporteventdata_by_event_id(event_id: str) -> SportEventData:
    result = await get_sporteventdata(event_id=event_id)
    if not result:
        raise ValueError(f"SportEvent with id '{event_id}' not found.")
    return result


@app.get(
    "/event/{event_id}/offer/{offer_type}",
    response_model_exclude_none=True,
    tags=["SportEvents"],
    operation_id="get_sportevent_offers",
)
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


@app.get(
    "/team",
    response_model_exclude_none=True,
    tags=["Teams"],
    summary="Get teams",
    operation_id="get_teams",
)
async def teams():
    return await get_teams()


@app.get(
    "/team/{team_abbr}/events",
    response_model_exclude_none=True,
    tags=["SportEvents", "Teams"],
    summary="Get sport events for a team",
    operation_id="get_team_events",
)
async def team_events(team_abbr: str):
    return await get_events_by_teamabbr(team_abbr)


@app.get(
    "/team/{team_abbr}/offers",
    response_model_exclude_none=True,
    tags=["SportEvents", "Teams"],
    summary="Get event offers for a team",
    operation_id="get_team_event_offers",
)
async def team_event_offers(team_abbr: str) -> list[EventOffer]:
    team = await get_team_by_abbr(team_abbr)
    if not team or not team.team_nick:
        raise ValueError(f"Team with abbreviation '{team_abbr}' not found.")
    return await get_team_event_offers(team_abbr)


@app.get(
    "/linemoves",
    response_model_exclude_none=True,
    tags=["OddsChanges"],
    summary="Get line moves for sport events",
    operation_id="get_linemoves",
)
async def linemoves() -> list[EventLineMovesResponse]:
    return await get_linemoves()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_level=LOG_LEVEL)

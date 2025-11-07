import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from prometheus_fastapi_instrumentator import Instrumentator

from oddstracker.config import APP_PORT, LOG_LEVEL
from oddstracker.service import PG_CLIENT
from oddstracker.service.oddschanges import get_all_changes
from oddstracker.service.oddscollector import collect_and_store_bettingdata
from oddstracker.service.oddsretriever import (
    get_bet_offers,
    get_event,
    get_events,
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

    # Startup
    await PG_CLIENT.initialize()
    logging.info("PostgresClient initialized.")

    logging.info("Application startup complete.")
    yield
    logging.info("Application shutdown starting.")

    # Shutdown - cleanup if needed
    await PG_CLIENT.close()
    logging.info("PostgresClient connection closed.")

    logging.info("Application shutdown complete.")


app = FastAPI(lifespan=lifespan)
add_pagination(app)

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
logging.info("Prometheus metrics instrumentation configured.")


@app.get("/")
def health():
    return {"status": "running"}


@app.post("/collect")
async def collect(provider_key="kambi", league="nfl"):
    return await collect_and_store_bettingdata(provider_key=provider_key, league=league)


@app.get("/event", response_model_exclude_none=True)
async def sportevents():
    return await get_events()


@app.get("/event/{event_id}", response_model_exclude_none=True)
async def sportevent(event_id: str):
    return await get_event(event_id)


@app.get("/event/{event_id}/offer/{offer_type}", response_model_exclude_none=True)
async def eventoffer(event_id: str, offer_type: str, range: bool = False):
    return await get_bet_offers(
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
async def team_event_offers(team_abbr: str):
    team = await get_team_by_abbr(team_abbr)
    if not team or not team.team_nick:
        raise ValueError(f"Team with abbreviation '{team_abbr}' not found.")
    return await get_team_event_offers(team_abbr)


@app.get("/changes", response_model_exclude_none=True)
async def changes():
    return await get_all_changes()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_level=LOG_LEVEL)

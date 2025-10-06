from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from oddstracker.config import APP_PORT, ROOT_DIR
from oddstracker.service import PG_CLIENT
from oddstracker.service.oddschanges import get_all_changes
from oddstracker.service.oddscollector import collect_and_store_kdata
from oddstracker.service.oddsretriever import (
    get_bet_offers,
    get_event,
    get_event_offer,
    get_events,
)
from oddstracker.service.teamprofiler import (
    get_team_event_offers,
    get_team_events,
    get_teams,
)
from oddstracker.utils import validate_betoffer_type

load_dotenv(ROOT_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    await PG_CLIENT.initialize()
    yield
    # Shutdown - cleanup if needed
    await PG_CLIENT.close()


app = FastAPI()


@app.get("/")
def health():
    return {"status": "running"}


@app.post("/collect")
async def collect():
    return await collect_and_store_kdata()


@app.get("/events", response_model_exclude_none=True)
async def events():
    return await get_events()


@app.get("/event/{event_id}", response_model_exclude_none=True)
async def event(event_id: int):
    return await get_event(event_id)


@app.get("/event/{event_id}/offers/{offer}", response_model_exclude_none=True)
async def event_offer(event_id: int, offer: str):
    return await get_event_offer(event_id, offer=validate_betoffer_type(offer))


@app.get("/event/{event_id}/offers", response_model_exclude_none=True)
async def bet_offers(event_id: int, range: bool = False):
    return await get_bet_offers(event_id, range_query=range)


@app.get("/changes", response_model_exclude_none=True)
async def changes():
    return await get_all_changes()


@app.get("/teams", response_model_exclude_none=True)
async def teams():
    return await get_teams()


@app.get("/team/{team_abbr}/events", response_model_exclude_none=True)
async def team_events(team_abbr: str):
    return await get_team_events(team_abbr)


@app.get("/team/{team_abbr}/offers", response_model_exclude_none=True)
async def team_event_offers(team_abbr: str):
    return await get_team_event_offers(team_abbr)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_level="info")

from dotenv import load_dotenv
from fastapi import FastAPI

from oddstracker.config import APP_PORT, ROOT_DIR
from oddstracker.domain.model.sportsbetting import BET_OFFER_TYPES
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

app = FastAPI()

load_dotenv(ROOT_DIR)


@app.get("/")
def health():
    return {"status": "running"}


@app.post("/collect")
def collect():
    return collect_and_store_kdata()


@app.get("/events", response_model_exclude_none=True)
def events():
    return get_events()


@app.get("/event/{event_id}", response_model_exclude_none=True)
def event(event_id: int):
    return get_event(event_id)


@app.get("/event/{event_id}/offers/{offer}", response_model_exclude_none=True)
def event_offer(event_id: int, offer: str):
    if offer == "moneyline":
        offer = "match"
    if offer == "pointspread":
        offer = "handicap"
    if offer not in BET_OFFER_TYPES:
        raise ValueError(f"Invalid offer type: {offer}. Valid types: {BET_OFFER_TYPES}")
    return get_event_offer(event_id, offer=offer)


@app.get("/event/{event_id}/offers", response_model_exclude_none=True)
def bet_offers(event_id: int, range: bool = False):
    return get_bet_offers(event_id, range_query=range)


@app.get("/changes", response_model_exclude_none=True)
def changes():
    return get_all_changes()


@app.get("/teams", response_model_exclude_none=True)
def teams():
    return get_teams()


@app.get("/team/{team_abbr}/events", response_model_exclude_none=True)
def team_events(team_abbr: str):
    return get_team_events(team_abbr)


@app.get("/team/{team_abbr}/offers", response_model_exclude_none=True)
def team_event_offers(team_abbr: str):
    return get_team_event_offers(team_abbr)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_level="info")

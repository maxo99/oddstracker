from dotenv import load_dotenv
from fastapi import FastAPI

from oddstracker.config import APP_PORT, ROOT_DIR
from oddstracker.service.oddscollector import collect_and_store_kdata
from oddstracker.service.oddsretriever import get_bet_offers, get_event, get_events

app = FastAPI()

load_dotenv(ROOT_DIR)


@app.get("/")
def health():
    return {"status": "running"}


@app.post("/collect")
def collect():
    return collect_and_store_kdata()


@app.get("/events")
def events():
    return get_events()


@app.get("/event/{event_id}")
def event(event_id: int):
    return get_event(event_id)


@app.get("/event/{event_id}/offers")
def bet_offers(event_id: int):
    return get_bet_offers(event_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)

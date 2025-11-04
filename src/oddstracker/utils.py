import json
import logging
import os
from datetime import UTC, datetime

import pydantic

from oddstracker.config import DATA_DIR

logger = logging.getLogger(__name__)


BET_OFFER_TYPES = ["h2h", "totals", "spreads"]


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, pydantic.BaseModel):
            return o.model_dump(mode="json", exclude_none=True)
        return super().default(o)


def get_utc_now():
    return datetime.now(UTC)


def sign_int(v) -> str:
    if isinstance(v, str) and not v.startswith("-"):
        if int(v) > 0:
            return f"+{v}"
        else:
            return str(v)
    return str(v)


def store_json(name: str, tag: str, data: dict) -> None:
    try:
        _name = "_".join([tag, name, get_utc_now().strftime("%Y-%m-%d")])
        path = os.path.join(DATA_DIR, _name + ".json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, cls=JsonEncoder)
    except Exception as e:
        logger.warning(f"Unable to store JSON data for {name} with tag {tag}: {e}")


def load_json(name: str, tag: str) -> dict:
    files = [f for f in os.listdir(DATA_DIR) if f.startswith(f"{tag}_{name}_")]
    if not files:
        raise FileNotFoundError(f"No file found for {tag}_{name}_* in {DATA_DIR}")
    files.sort(reverse=True)
    _name = files[0]
    path = os.path.join(DATA_DIR, _name)
    with open(path) as f:
        data = json.load(f)
    return data


def validate_betoffer_type(offer: str):
    if offer == "moneyline":
        return "match"
    if offer == "pointspread":
        return "handicap"
    if offer not in BET_OFFER_TYPES:
        raise ValueError(f"Invalid offer type: {offer}. Valid types: {BET_OFFER_TYPES}")
    return offer

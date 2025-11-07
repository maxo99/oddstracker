import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import nfl_data_py as nfl

from oddstracker.domain.model.sportevent import SportEvent, SportEventData

_names = ["h2h", "spreads", "totals"]

logger = logging.getLogger(__name__)

TEAMS = nfl.import_team_desc()
SCHEDULES = nfl.import_schedules([2025])


class KambiConverter:
    @classmethod
    def from_dict(cls, data: dict) -> list[SportEventData]:
        try:
            return [cls.transform_kambi_event(event) for event in data.get("events", [])]
        except Exception as e:
            raise e

    @classmethod
    def transform_kambi_event(cls, _input: dict) -> SportEventData:
        try:
            _input.update(**_input.pop("event"))
            del _input["tags"]
            del _input["path"]
            del _input["nonLiveBoCount"]
            del _input["state"]
            del _input["englishName"]
            _input.pop("extraInfo", None)
            del _input["name"]
            del _input["nameDelimiter"]
            del _input["groupId"]
            _input["commence_time"] = _input.pop("start")
            _input["sport_key"] = (
                _input.pop("sport").strip("_").lower() + "_" + _input["group"].lower()
            )
            _input["sport_title"] = _input.pop("group")
            _input["home_team"] = cls._kambi_map_team_name(_input.pop("homeName"))
            _input["away_team"] = cls._kambi_map_team_name(_input.pop("awayName"))
            _input["id"] = get_nfldatapy_event_id(
                _input["home_team"],
                _input["away_team"],
                _input["commence_time"],
            )

            offers = []
            for bo in _input.pop("betOffers"):
                for o in bo["outcomes"]:
                    _offer = {
                        "event_id": str(_input["id"]),
                        "offer_type": cls._map_kambi_market_key(bo["betOfferType"]["name"]),
                        "bookmaker": "kambi",
                        "timestamp": datetime.fromisoformat(
                            o["changedDate"].replace("Z", "+00:00")
                        ),
                        "price": o["odds"] / 1000,
                    }
                    if _offer["offer_type"] == "h2h":
                        _offer["choice"] = o["participant"]
                    else:
                        _offer["choice"] = o["label"]
                        _offer["point"] = o["line"] / 1000
                    offers.append(_offer)

            return SportEventData(event=SportEvent(**_input), offers=offers)
        except Exception as e:
            raise e

    @staticmethod
    def _kambi_map_team_name(input):
        return TEAMS.loc[
            TEAMS["team_nick"] == input.split(" ")[-1],
            "team_abbr",
        ].values[0]

    @staticmethod
    def _map_kambi_market_key(input):
        match input.lower():
            case "match":
                return "h2h"
            case "handicap":
                return "spreads"
            case "over/under":
                return "totals"


def _toa_to_nfldatapy(_input: dict):
    _input["home_team"] = TEAMS.loc[
        TEAMS["team_name"] == _input["home_team"],
        "team_abbr",
    ].values[0]
    _input["away_team"] = TEAMS.loc[
        TEAMS["team_name"] == _input["away_team"],
        "team_abbr",
    ].values[0]

    _input["id"] = get_nfldatapy_event_id(
        _input["home_team"],
        _input["away_team"],
        _input["commence_time"],
    )


def get_nfldatapy_event_id(home_team: str, away_team: str, game_day: str) -> str:
    try:
        # Parse the UTC datetime and convert to Eastern Time
        utc_time = datetime.strptime(game_day, "%Y-%m-%dT%H:%M:%SZ")
        utc_time = utc_time.replace(tzinfo=ZoneInfo("UTC"))
        eastern_time = utc_time.astimezone(ZoneInfo("America/New_York"))
        _game_day_str = eastern_time.strftime("%Y-%m-%d")

        event_id = SCHEDULES[
            (SCHEDULES["home_team"] == home_team)
            & (SCHEDULES["away_team"] == away_team)
            & (SCHEDULES["gameday"] == _game_day_str)
        ]["game_id"].values[0]
        logger.info(f"Mapped event id using nfl_data_py: {event_id}")
        return str(event_id)
    except Exception as e:
        logger.warning(f"Could not map event id using nfl_data_py: {e}")
        return f"{home_team}_{away_team}_{game_day}"


def transform_theoddsapi_event(_input: dict) -> SportEventData:
    try:
        offers = []
        _toa_to_nfldatapy(_input)
        for bm in _input.pop("bookmakers", []):
            for mk in bm.get("markets", []):
                for outcome in mk.get("outcomes", []):
                    outcome = {
                        "event_id": _input["id"],
                        "offer_type": mk["key"],
                        "bookmaker": bm["key"],
                        "choice": outcome["name"],
                        "price": outcome["price"],
                        "timestamp": datetime.fromisoformat(
                            bm["last_update"].replace("Z", "+00:00")
                        ),
                    }
                    offers.append(outcome)
        return SportEventData(event=SportEvent(**_input), offers=offers)
    except Exception as e:
        raise e


def convert_to_sportevents(
    provider_key: str,
    data: dict | list[dict],
) -> list[SportEventData]:
    out = []
    try:
        if provider_key == "theoddsapi":
            out.extend(transform_theoddsapi_event(e) for e in data)
        elif provider_key == "kambi" and isinstance(data, dict):
            out.extend(KambiConverter.from_dict(data))
        return out
    except Exception as ex:
        logger.error("Failed to parse sporteventdatas")
        raise ex

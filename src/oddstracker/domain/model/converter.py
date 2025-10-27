import logging

from oddstracker.domain.model.sportevent import SportEvent, SportEventData

_names = ["h2h", "spreads", "totals"]

logger = logging.getLogger(__name__)


def _map_kambi_market_key(input):
    match input.lower():
        case "match":
            return "h2h"
        case "handicap":
            return "spreads"
        case "over/under":
            return "totals"


def _map_team_name(input):
    # TODO: Update implementation
    return input


def transform_kambi_event(_input: dict) -> SportEventData:
    try:
        _input.update(**_input.pop("event"))
        _input["id"] = str(_input["id"])
        del _input["tags"]
        del _input["path"]
        del _input["nonLiveBoCount"]
        del _input["state"]
        del _input["englishName"]
        # del se["participants"]
        _input.pop("extraInfo", None)
        del _input["name"]
        del _input["nameDelimiter"]
        del _input["groupId"]
        _input["commence_time"] = _input.pop("start")
        _input["sport_key"] = (
            _input.pop("sport").strip("_").lower() + "_" + _input["group"].lower()
        )
        _input["sport_title"] = _input.pop("group")
        _input["id"] = str(_input.pop("id"))
        _input["home_team"] = _map_team_name(_input.pop("homeName"))
        _input["away_team"] = _map_team_name(_input.pop("awayName"))

        offers = []
        for bo in _input.pop("betOffers"):
            for o in bo["outcomes"]:
                _offer = {
                    "event_id": str(_input["id"]),
                    "offer_type": _map_kambi_market_key(bo["betOfferType"]["name"]),
                    "bookmaker": "kambi",
                    "last_update": o["changedDate"],
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


def transform_theoddsapi_event(_input: dict) -> SportEventData:
    try:
        offers = []
        for bm in _input.pop("bookmakers", []):
            for mk in bm.get("markets", []):
                for outcome in mk.get("outcomes", []):
                    outcome = {
                        'event_id': _input["id"],
                        'offer_type': mk["key"],
                        'last_update': bm["last_update"],
                        'bookmaker': bm["key"],
                        'choice': outcome["name"],
                        'price': outcome["price"],
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
        elif provider_key == "kambi":
            out.extend(transform_kambi_event(data) for data in data["events"])
        return out
    except Exception as ex:
        logger.error("Failed to parse sporteventdatas")
        raise ex
    return out

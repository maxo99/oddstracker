import datetime

BET_OFFER_TYPES = ["match", "handicap", "overunder"]


def get_utc_now():
    return datetime.datetime.now(datetime.UTC)


def sign_int(v) -> str:
    if isinstance(v, str) and not v.startswith("-"):
        if int(v) > 0:
            return f"+{v}"
        else:
            return str(v)
    return str(v)


def validate_betoffer_type(offer: str):
    if offer == "moneyline":
        return "match"
    if offer == "pointspread":
        return "handicap"
    if offer not in BET_OFFER_TYPES:
        raise ValueError(f"Invalid offer type: {offer}. Valid types: {BET_OFFER_TYPES}")
    return offer

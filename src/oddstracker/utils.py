import datetime


def get_utc_now():
    return datetime.datetime.now(datetime.UTC)


def sign_int(v) -> str:
    if isinstance(v, str) and not v.startswith("-"):
        if int(v) > 0:
            return f"+{v}"
        else:
            return str(v)
    return str(v)

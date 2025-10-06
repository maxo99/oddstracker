from pydantic import BaseModel

PROVIDERS = [
    {
        "sportsbook": "ilani Casino",
        "site_code": "ilaniuswarl",
        "site_specials_name": "ilani",
    },
    # {
    #     "sportsbook": "Barstool",
    #     "site_code": "pivuspa",
    #     "site_specials_name": "barstool",
    # },
    # {
    #     "sportsbook": "DraftKings",
    #     "site_code": "rsiuspa",
    #     "site_specials_name": "draftkings",
    # },
]


class KambiProvider(BaseModel):
    sportsbook: str
    site_code: str
    site_specials_name: str
    base_url: str | None = None
    ncaa_url: str = ""
    nfl_url: str = ""
    sport: str = "american_football"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.base_url = (
            f"https://eu-offering-api.kambicdn.com/offering/v2018/{self.site_code}"
        )
        self.ncaa_url = (
            f"{self.base_url}/listView/{self.sport}/ncaaf/all/all/matches.json"
        )

        self.nfl_url = f"{self.base_url}/listView/{self.sport}/nfl/all/all/matches.json"

        # return self

    def qparams(self, props: bool = False) -> dict:
        if props:
            return {
                "lang": "en_US",
                "market": "US",
                "includeParticipants": "true",
            }
        return {
            "lang": "en_US",
            "market": "US",
            "useCombined": "true",
            "useCombinedLive": "true",
            "includeParticipants": "true",
            # range_start = list("0"),
            # range_size = list("0")
        }

    def get_player_props_url(self, event_id: str) -> str:
        return f"{self.base_url}/betoffer/event/{event_id}.json"


PROVIDER = KambiProvider(**PROVIDERS[0])

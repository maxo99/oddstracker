from abc import ABC, abstractmethod

from pydantic import BaseModel

from oddstracker.config import TOA_API_KEY

KAMBI_PROVIDERS = [
    {
        "provider_key": "kambi",
        "sportsbook": "ilani Casino",
        "site_code": "ilaniuswarl",
        "site_specials_name": "ilani",
        "base_url": "https://eu-offering-api.kambicdn.com/offering/v2018/ilaniuswarl",
    },
    # {
    # 'provider_key': 'kambi-cdn',
    #     "sportsbook": "Barstool",
    #     "site_code": "pivuspa",
    #     "site_specials_name": "barstool",
    # },
    # {
    # 'provider_key': 'kambi-cdn',
    #     "sportsbook": "DraftKings",
    #     "site_code": "rsiuspa",
    #     "site_specials_name": "draftkings",
    # },
]

TOA_PROVIDERS = [
    {

    }
]



class Provider(BaseModel, ABC):
    provider_key: str


    @abstractmethod
    def get_url(self, *args, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def qparams(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    def __str__(self) -> str:
        return f"Provider({self.provider_key})"


class KambiProvider(Provider):
    provider_key: str = "kambi-cdn"
    sportsbook: str
    site_code: str
    site_specials_name: str
    base_url: str

    def get_url(self, league: str, event_id: str | None = None) -> str:
        if event_id:
            return f"{self.base_url}/betoffer/event/{event_id}.json"
        if league == "nfl":
            return (
                f"{self.base_url}/listView/american_football/nfl/all/all/matches.json"
            )
        if league == "ncaaf":
            return (
                f"{self.base_url}/listView/american_football/ncaaf/all/all/matches.json"
            )
        raise ValueError(f"Unsupported league: {league}")

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


class TheOddsAPIProvider(Provider):
    ## https://github.com/the-odds-api/samples-python/blob/master/odds.py
    ## https://the-odds-api.com/liveapi/guides/v4/
    provider_key: str = "theoddsapi"
    sportsbook: str = "TheOddsAPI"
    site_code: str = "theoddsapi"

    def get_url(self, league: str) -> str:
        if league == 'nfl':
            return "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
        raise ValueError

    def qparams(self):
        ODDS_FORMAT = "decimal"
        REGIONS = "us2"
        MARKETS = "h2h,spreads,totals"
        return {
            "api_key": TOA_API_KEY,
            "regions": REGIONS,
            "markets": MARKETS,
            "oddsFormat": ODDS_FORMAT,
            "dateFormat": "iso",
        }

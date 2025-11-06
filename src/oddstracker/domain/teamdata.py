from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel

NFL_DATA_PI_ABBR_TO_KAMBIDATA = {
    "ARI": {"participant": "ARI Cardinals", "id": 1000043092},
    "ATL": {"participant": "ATL Falcons", "id": 1000068767},
    "BAL": {"participant": "BAL Ravens", "id": 1000049533},
    "BUF": {"participant": "BUF Bills", "id": 1000017217},
    "CAR": {"participant": "CAR Panthers", "id": 1000000638},
    "CHI": {"participant": "CHI Bears", "id": 1000000178},
    "CIN": {"participant": "CIN Bengals", "id": 1000056258},
    "CLE": {"participant": "CLE Browns", "id": 1000031301},
    "DAL": {"participant": "DAL Cowboys", "id": 1000020068},
    "DEN": {"participant": "DEN Broncos", "id": 1000000177},
    "DET": {"participant": "DET Lions", "id": 1000047062},
    "GB": {"participant": "GB Packers", "id": 1000055908},
    "HOU": {"participant": "HOU Texans", "id": 1000080350},
    "IND": {"participant": "IND Colts", "id": 1000000174},
    "JAX": {"participant": "JAX Jaguars", "id": 1000067383},
    "KC": {"participant": "KC Chiefs", "id": 1000091850},
    "LAC": {"participant": "LA Chargers", "id": 1000037375},
    "LAR": {"participant": "LA Rams", "id": 1000083544},
    "LV": {"participant": "LV Raiders", "id": 1000085238},
    "MIA": {"participant": "MIA Dolphins", "id": 1000074777},
    "MIN": {"participant": "MIN Vikings", "id": 1000029137},
    "NE": {"participant": "NE Patriots", "id": 1000000175},
    "NO": {"participant": "NO Saints", "id": 1000062103},
    "NYG": {"participant": "NY Giants", "id": 1000070038},
    "NYJ": {"participant": "NY Jets", "id": 1000019658},
    "PHI": {"participant": "PHI Eagles", "id": 1000065021},
    "PIT": {"participant": "PIT Steelers", "id": 1000000176},
    "SEA": {"participant": "SEA Seahawks", "id": 1000000333},
    "SF": {"participant": "SF 49ers", "id": 1000030413},
    "TB": {"participant": "TB Buccaneers", "id": 1000086605},
    "TEN": {"participant": "TEN Titans", "id": 1000058218},
    "WAS": {"participant": "WAS Commanders", "id": 1000000334},
}


class TeamData(SQLModel, table=True):
    """
    SQLModel representing NFL team data from nfl_data_py.import_team_desc()
    """

    # Primary key
    team_abbr: str = Field(sa_column=Column(String, primary_key=True, nullable=False))

    # Basic team information
    team_name: str = Field(description="Full team name (e.g., 'Arizona Cardinals')")
    team_id: str = Field(description="nfl_data_py team identifier")
    team_nick: str = Field(description="Team nickname (e.g., 'Cardinals')")
    team_conf: str = Field(description="Conference (AFC/NFC)")
    team_division: str = Field(description="Division (e.g., 'NFC West')")

    # Team colors
    team_color: str = Field(description="Primary team color (hex code)")
    team_color2: str | None = Field(
        default=None, description="Secondary team color (hex code)"
    )
    team_color3: str | None = Field(
        default=None, description="Tertiary team color (hex code)"
    )
    team_color4: str | None = Field(
        default=None, description="Quaternary team color (hex code)"
    )

    # Logo and image URLs
    team_logo_wikipedia: str | None = Field(
        default=None,
        description="Wikipedia logo URL",
    )
    team_logo_espn: str | None = Field(
        default=None,
        description="ESPN logo URL",
    )
    team_wordmark: str | None = Field(
        default=None,
        description="Team wordmark URL",
    )
    team_conference_logo: str | None = Field(
        default=None,
        description="Conference logo URL",
    )
    team_league_logo: str | None = Field(
        default=None,
        description="NFL league logo URL",
    )
    team_logo_squared: str | None = Field(
        default=None,
        description="Squared team logo URL",
    )

    # TODO: remove Kambi specific fields later
    participant_name: str | None = Field(
        default=None,
        description="Kambi participant name mapping",
    )
    participant_id: int | None = Field(
        default=None,
        description="Kambi participant ID mapping",
    )

    def populate_kambi_fields(self) -> "TeamData":
        if not self.participant_name or not self.participant_id:
            self.participant_name = NFL_DATA_PI_ABBR_TO_KAMBIDATA[self.team_abbr][
                "participant"
            ]
            self.participant_id = NFL_DATA_PI_ABBR_TO_KAMBIDATA[self.team_abbr]["id"]
        return self

    @staticmethod
    def _clean_value(value) -> str | None:
        """Convert pandas NaN to None, otherwise return the value as string"""
        if value is None or (isinstance(value, float) and str(value) == "nan"):
            return None
        return str(value) if value is not None else None

    @classmethod
    def from_nfl_data(cls, df_row) -> "TeamData":
        """
        Create a TeamData instance from a row of nfl_data_py.import_team_desc() DataFrame

        Args:
            df_row: A pandas Series representing a single row from the NFL team data

        Returns:
            TeamData instance
        """
        _cls = cls(
            team_abbr=df_row["team_abbr"],
            team_name=df_row["team_name"],
            team_id=str(df_row["team_id"]),
            team_nick=df_row["team_nick"],
            team_conf=df_row["team_conf"],
            team_division=df_row["team_division"],
            team_color=df_row["team_color"],
            team_color2=cls._clean_value(df_row.get("team_color2")),
            team_color3=cls._clean_value(df_row.get("team_color3")),
            team_color4=cls._clean_value(df_row.get("team_color4")),
            team_logo_wikipedia=cls._clean_value(df_row.get("team_logo_wikipedia")),
            team_logo_espn=cls._clean_value(df_row.get("team_logo_espn")),
            team_wordmark=cls._clean_value(df_row.get("team_wordmark")),
            team_conference_logo=cls._clean_value(df_row.get("team_conference_logo")),
            team_league_logo=cls._clean_value(df_row.get("team_league_logo")),
            team_logo_squared=cls._clean_value(df_row.get("team_logo_squared")),
        )
        return _cls.populate_kambi_fields()

    @property
    def location(self) -> str:
        return " ".join(self.team_name.split()[:-1])

    @property
    def searchTags(self) -> list[str]:
        return [self.team_abbr, self.location, self.team_nick]

import logging

from oddstracker.domain.model.sportsbetting import BetOffer, SportsBettingInfo, SportsEvent

logger = logging.getLogger(__name__)


def test_kambi_data_load(sample_events):
    participants = {}
    for i, e in enumerate(sample_events):
        logger.info(f"Parsing event:{i} {e['event']['englishName']}")
        try:
            kdata = SportsBettingInfo(**e)
            participants = {**participants, **kdata.participants}
            logger.info(f"Parsed: {kdata}")
            assert isinstance(kdata, SportsBettingInfo)
            assert isinstance(kdata.event, SportsEvent)
            assert isinstance(kdata.betOffers, list)
            assert isinstance(kdata.betOffers[0], BetOffer)
            assert isinstance(kdata.betOffers[0].type, str)
        except Exception as ex:
            logger.error(f"Failed to parse event: {e['event']['englishName']}")
            raise ex
    assert True
    logger.info(f"Parsed {len(sample_events)} events")
    out = {}
    for id, participant in participants.items():
        out[participant.split(" ")[0]] = dict(participant=participant, id=id)
    logger.info(f"Participants:  \n {out}")


def test_teams_loading():
    from oddstracker.service.teamprofiler import get_teams

    teams = get_teams()
    assert isinstance(teams, list)
    assert len(teams) > 0
    for team in teams:
        assert team.participant_id is not None
        assert team.participant_name is not None
        assert team.team_abbr is not None
        assert team.team_name is not None
        assert team.team_division is not None
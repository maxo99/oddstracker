import logging
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, select

from oddstracker import config
from oddstracker.domain.model.sportsbetting import BetOffer, SportsEvent
from oddstracker.domain.teamdata import TeamData
from oddstracker.utils import get_utc_now

logger = logging.getLogger(__name__)


class PostgresClient:
    def __init__(self, db_url: str | None = None, use_null_pool: bool = False):
        try:
            logger.info("Initializing Postgres client")
            self.db_url = db_url or config.get_pg_url()
            if self.db_url.startswith("postgresql://"):
                self.db_url = self.db_url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )

            engine_kwargs = {"poolclass": NullPool} if use_null_pool else {}
            self.engine = create_async_engine(self.db_url, **engine_kwargs)
            self.session_maker = async_sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )
        except Exception as e:
            logger.error(f"Error initializing Postgres client: {e}")
            raise e

    async def get_session(self):
        """Dependency to get database session. Use with FastAPI Depends."""
        async with self.session_maker() as session:
            yield session

    async def initialize(self):
        """Initialize database tables. Call this after creating the client."""
        await self._create_tables()

    async def _create_tables(self):
        """Create tables if they don't exist"""
        try:
            async with self.engine.begin() as conn:
                # await conn.run_sync(lambda sync_conn: sync_conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector")))
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Postgres tables created/checked successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise e

    async def validate_connection(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Postgres connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Error validating Postgres connection: {e}")
            return False

    async def close(self):
        try:
            await self.engine.dispose()
            logger.info("Closed Postgres client connection")
        except Exception as e:
            logger.error(f"Error closing Postgres client connection: {e}")
            raise e

    async def add_event_and_betoffers(
        self, event: SportsEvent, bet_offers: list[BetOffer]
    ):
        logger.info(f"Upserting event {event.id} and {len(bet_offers)} betoffers.")
        async with self.session_maker() as session:
            try:
                # with session.begin_nested():
                await self._upsert_event(event, session)
                # with session.begin_nested():
                await self._upsert_betoffers(bet_offers, session)
                await session.commit()
            except Exception as e:
                logger.error(f"Error upserting events and betoffers: {e}")
                await session.rollback()
                raise e

    async def _upsert_betoffers(self, bet_offers, session):
        try:
            for bo in bet_offers:
                logger.info(f"Upserting bet offer {bo.id} for event {bo.event_id}.")
                result = await session.execute(
                    select(BetOffer).where(BetOffer.id == bo.id, BetOffer.active)
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    session.add(bo)
                else:
                    # outcomes is stored as JSON (list of dicts), so access as dict
                    if (
                        existing.outcomes[0]["changedDate"]
                        == bo.outcomes[0]["changedDate"]
                    ):
                        existing.updated_at = get_utc_now()
                    else:
                        bo.updated_at = get_utc_now()
                        existing.active = False
                        session.merge(bo)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error adding bet offers: {e.__cause__}")
            raise e

    async def _upsert_event(self, event, session):
        try:
            existing = await session.get(SportsEvent, event.id)
            if not existing:
                session.add(event)
            else:
                # State was updated, mark existing as deleted and insert new
                if existing.state != event.state:
                    # Update Existing
                    existing.updated_at = get_utc_now()

                    event.created_at = existing.created_at
                    event.updated_at = get_utc_now()
                    session.merge(event)
                else:
                    existing.updated_at = get_utc_now()
            logger.info(f"Upserted event {event.id} successfully.")
        except Exception as e:
            logger.error(f"Error adding event {event.id}: {e}")
            raise e

    async def get_events(self, **filters) -> list[SportsEvent]:
        try:
            logger.info(f"Fetching events from with {filters}")
            async with self.session_maker() as session:
                query = select(SportsEvent)

                # if not include_deleted:
                #     query = query.where(KambiEvent.deleted_at is None)

                if filters:
                    for key, value in filters.items():
                        if key.startswith("not_"):
                            actual_key = key[4:]
                            query = query.where(
                                getattr(SportsEvent, actual_key) != value
                            )
                        else:
                            query = query.where(getattr(SportsEvent, key) == value)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise e

    async def get_event(self, event_id: int) -> SportsEvent | None:
        try:
            logger.info(f"Fetching event with ID {event_id}")
            async with self.session_maker() as session:
                event = await session.get(SportsEvent, event_id)
                return event
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise e

    async def get_bet_offers_for_event(
        self, event_id: int, offer: str | None = None, range_query: bool = False
    ) -> list[BetOffer]:
        try:
            logger.info(
                f"Fetching bet offers for event ID {event_id} (range={range_query})"
            )
            async with self.session_maker() as session:
                if range_query:
                    result = await session.execute(
                        text(
                            "SELECT DISTINCT ON (id) * FROM betoffer "
                            'WHERE "event_id" = :event_id '
                            "ORDER BY id, collected_at ASC"
                        ),
                        {"event_id": event_id},
                    )
                    first_offers = {
                        row.id: BetOffer(**dict(row._mapping))
                        for row in result.fetchall()
                    }

                    result = await session.execute(
                        text(
                            "SELECT DISTINCT ON (id) * FROM betoffer "
                            'WHERE "event_id" = :event_id '
                            "ORDER BY id, collected_at DESC"
                        ),
                        {"event_id": event_id},
                    )
                    last_offers = {
                        row.id: BetOffer(**dict(row._mapping))
                        for row in result.fetchall()
                    }

                    bet_offers = []
                    for bet_offer_id, first_offer in first_offers.items():
                        last_offer = last_offers.get(bet_offer_id)
                        if last_offer:
                            bet_offers.append(first_offer)
                            bet_offers.append(last_offer)
                    return bet_offers
                else:
                    query = select(BetOffer).where(BetOffer.event_id == event_id)
                    if offer:
                        query = query.where(BetOffer.type == offer)
                    result = await session.execute(query)
                    bet_offers = list(result.scalars().all())
                    return bet_offers
        except Exception as e:
            logger.error(f"Error getting bet offers for event {event_id}: {e}")
            raise e

    async def get_bet_offer_history(
        self, bet_offer_id: int, event_id: int, limit: int = 2
    ) -> list[BetOffer]:
        try:
            logger.debug(f"Fetching history for bet offer {bet_offer_id}")
            async with self.session_maker() as session:
                result = await session.execute(
                    text(
                        'SELECT * FROM betoffer WHERE id = :bet_offer_id AND "event_id" = :event_id '
                        "ORDER BY collected_at DESC LIMIT :limit"
                    ),
                    {
                        "bet_offer_id": bet_offer_id,
                        "event_id": event_id,
                        "limit": limit,
                    },
                )
                rows = result.fetchall()
                bet_offers = []
                for row in rows:
                    bet_offer = BetOffer(**dict(row._mapping))
                    bet_offers.append(bet_offer)
                return bet_offers
        except Exception as e:
            logger.error(f"Error getting bet offer history: {e}")
            raise e

    async def add_teamdata(self, teamdata: list[TeamData]):
        try:
            logger.info(f"Upserting teamdata {len(teamdata)}.")
            async with self.session_maker() as session:
                # if none exist add all

                result = await session.execute(select(TeamData).limit(1))
                if not result.first():
                    session.add_all(teamdata)
                    await session.commit()
                    logger.info(
                        f"Upserted teamdata {[td.team_id for td in teamdata]} successfully."
                    )
        except Exception as e:
            logger.error(f"Error upserting teamdata: {e}")
            raise e

    async def get_teams(self) -> list[TeamData]:
        try:
            logger.info("Fetching all teams from DB")
            async with self.session_maker() as session:
                query = select(TeamData)
                result = await session.execute(query)
                teams = list(result.scalars().all())
                return teams
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            raise e

    async def get_events_by_participant(
        self, participant_name: str
    ) -> list[SportsEvent]:
        try:
            logger.info(f"Fetching events for participant {participant_name}")
            async with self.session_maker() as session:
                query = (
                    select(SportsEvent).where(
                        (SportsEvent.homeName == participant_name)
                        | (SportsEvent.awayName == participant_name)
                    )
                    # .where(KambiEvent.deleted_at is None)
                )
                result = await session.execute(query)
                events = list(result.scalars().all())
                return events
        except Exception as e:
            logger.error(
                f"Error getting events for participant {participant_name}: {e}"
            )
            raise e

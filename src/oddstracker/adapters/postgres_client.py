import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, select

from oddstracker import config
from oddstracker.domain.model.sportevent import (
    EventOffer,
    SportEvent,
    SportEventData,
)
from oddstracker.domain.teamdata import TeamData

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

    async def add_sporteventdata(self, sportevent: SportEventData):
        logger.info(f"Upserting event {sportevent}")
        async with self.session_maker() as session:
            try:
                await self._upsert_sportevent(sportevent.event, session)
                await self._upsert_eventoffers(sportevent.offers, session)
                await session.commit()
            except Exception as e:
                logger.error(f"Error upserting events and betoffers: {e}")
                await session.rollback()
                raise e

    async def _upsert_eventoffers(self, offers: list[EventOffer], session):
        try:
            for bo in offers:
                logger.info(f"Upserting {bo}")
                session.add(bo)
            logger.info(f"Upserted {len(offers)} eventoffers successfully.")
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error adding eventoffers: {e.__cause__}")
            raise e

    async def _upsert_sportevent(self, sportevent: SportEvent, session):
        try:
            # existing = await session.get(SportEvent, sportevent.id)
            # if not existing:
            session.add(sportevent)
            # else:
            #     # State was updated, mark existing as deleted and insert new
            #     if existing.state != sportevent.state:
            #         # Update Existing
            #         existing.updated_at = get_utc_now()

            #         sportevent.created_at = existing.created_at
            #         sportevent.updated_at = get_utc_now()
            #         session.merge(sportevent)
            #     else:
            #         existing.updated_at = get_utc_now()
            logger.info(f"Upserted event {sportevent.id} successfully.")
        except Exception as e:
            logger.error(f"Error adding event {sportevent.id}: {e}")
            raise e

    async def get_events(self, **filters) -> list[SportEvent]:
        try:
            logger.info(f"Fetching events from with {filters}")
            async with self.session_maker() as session:
                query = select(SportEvent)
                # if not include_deleted:
                #     query = query.where(KambiEvent.deleted_at is None)

                if filters:
                    for key, value in filters.items():
                        if key.startswith("not_"):
                            actual_key = key[4:]
                            query = query.where(
                                getattr(SportEvent, actual_key) != value
                            )
                        else:
                            query = query.where(getattr(SportEvent, key) == value)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise e

    async def get_sporteventdata(self, event_id: str) -> SportEventData | None:
        try:
            logger.info(f"Fetching event with ID {event_id}")
            async with self.session_maker() as session:
                event = await session.get(SportEvent, event_id)
                if event is None:
                    return None

                offers = await self._fetch_eventoffers_for_sportevent(session, event_id)
                return SportEventData(event=event, offers=offers)

        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise e

    async def get_eventoffers_for_sportevent(
        self, event_id: int, offer_type: str | None = None, range_query: bool = False
    ) -> list[EventOffer]:
        try:
            logger.info(
                f"Fetching eventoffers for event ID {event_id} (range={range_query})"
            )
            async with self.session_maker() as session:
                return await self._fetch_eventoffers_for_sportevent(
                    session,
                    event_id,
                    offer_type=offer_type,
                    range_query=range_query,
                )
        except Exception as e:
            logger.error(f"Error getting eventoffers for event {event_id}: {e}")
            raise e

    async def _fetch_eventoffers_for_sportevent(
        self,
        session: AsyncSession,
        event_id: int,
        offer_type: str | None = None,
        range_query: bool = False,
    ) -> list[EventOffer]:
        try:
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
                    row.id: EventOffer(**dict(row._mapping))
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
                    row.id: EventOffer(**dict(row._mapping))
                    for row in result.fetchall()
                }

                event_offers = []
                for event_offer_id, first_offer in first_offers.items():
                    last_offer = last_offers.get(event_offer_id)
                    if last_offer:
                        event_offers.append(first_offer)
                        event_offers.append(last_offer)
                return event_offers

            query = select(EventOffer).where(EventOffer.event_id == event_id)
            if offer_type:
                query = query.where(EventOffer.offer_type == offer_type)
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"Error fetching eventoffers for event {event_id} within active session: {e}"
            )
            raise e

    async def get_eventoffer_history(
        self, offer_type: str, event_id: int, limit: int = 2
    ) -> list[EventOffer]:
        try:
            logger.debug(f"Fetching history for event:{event_id} offer {offer_type}")
            async with self.session_maker() as session:
                result = await session.execute(
                    text(
                        'SELECT * FROM betoffer WHERE offer_type = :offer_type AND "event_id" = :event_id '
                        "ORDER BY collected_at DESC LIMIT :limit"
                    ),
                    {
                        "offer_type": offer_type,
                        "event_id": event_id,
                        "limit": limit,
                    },
                )
                rows = result.fetchall()
                event_offers = []
                for row in rows:
                    event_offer = EventOffer(**dict(row._mapping))
                    event_offers.append(event_offer)
                return event_offers
        except Exception as e:
            logger.error(f"Error getting eventoffer history: {e}")
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
    ) -> list[SportEvent]:
        try:
            logger.info(f"Fetching events for participant {participant_name}")
            async with self.session_maker() as session:
                query = (
                    select(SportEvent).where(
                        (SportEvent.home_team == participant_name)
                        | (SportEvent.away_team == participant_name)
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

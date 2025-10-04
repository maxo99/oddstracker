import logging
from datetime import UTC, datetime

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

from oddstracker import config
from oddstracker.domain.kambi_event import BetOffer, KambiEvent

# from oddstracker.domain.kambi_event import Event, SQLModel

logger = logging.getLogger(__name__)


# @dataclass
# class SimilarityResponse:
#     events: list[Event]
#     scores: list[float]


class PostgresClient:
    def __init__(self, db_url: str | None = None):
        try:
            logger.info("Initializing Postgres client")
            self.db_url = db_url or config.get_pg_url()
            self.engine = create_engine(self.db_url)
            self.session_maker = sessionmaker(bind=self.engine)
            self._session = self.session_maker()

            with self.engine.connect() as conn:
                # conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()

            self._create_tables()
        except Exception as e:
            logger.error(f"Error initializing Postgres client: {e}")
            raise e

    def _create_tables(self):
        if "event" not in inspect(self.engine).get_table_names():
            logger.info("Creating Postgres tables if they do not exist")
            SQLModel.metadata.create_all(self.engine)
            logger.info("Postgres tables created/checked successfully")
        else:
            logger.warning(
                f"SQL tables already exist: {list(SQLModel.metadata.tables.keys())}"
            )

    def validate_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Postgres connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Error validating Postgres connection: {e}")
            return False

    def close(self):
        try:
            self._session.close()
            self.engine.dispose()
            logger.info("Closed Postgres client connection")
        except Exception as e:
            logger.error(f"Error closing Postgres client connection: {e}")
            raise e

    def add_event(self, event: KambiEvent, bet_offers: list[BetOffer]):
        try:
            logger.info(f"Upserting event {event.id}.")
            with self.session_maker() as session:


                existing = session.get(KambiEvent, event.id)

                if not existing:
                    session.add(event)
                else:
                    # TODO: Validate soft delete logic
                    if existing.deleted_at is None:
                        # State was updated, mark existing as deleted and insert new
                        if existing.state != event.state:
                            existing.deleted_at = datetime.now(UTC)
                            session.add(existing)
                            session.flush()

                            event.created_at = datetime.now(UTC)
                            event.updated_at = datetime.now(UTC)
                            session.merge(event)
                        else:
                            existing.updated_at = datetime.now(UTC)
                    else:
                        event.created_at = datetime.now(UTC)
                        event.updated_at = datetime.now(UTC)
                        session.merge(event)

                session.flush()

                try:
                    for bo in bet_offers:
                        session.add(bo)
                except Exception as e:
                    logger.error(f"Error adding bet offers for event {event.id}: {e}")
                    raise e

                session.commit()
                logger.info(f"Upserted event {event.id} successfully.")
        except Exception as e:
            logger.error(f"Error upserting events: {e}")
            raise e

    def get_events(self, include_deleted: bool = False, **filters) -> list[KambiEvent]:
        try:
            logger.info(f"Fetching events from with {filters}")
            with self.session_maker() as session:
                query = select(KambiEvent)

                if not include_deleted:
                    query = query.where(KambiEvent.deleted_at == None)

                if filters:
                    for key, value in filters.items():
                        if key.startswith("not_"):
                            actual_key = key[4:]
                            query = query.where(
                                getattr(KambiEvent, actual_key) != value
                            )
                        else:
                            query = query.where(getattr(KambiEvent, key) == value)
                return list(session.execute(query).scalars().all())
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise e

    def get_event(self, event_id: int) -> KambiEvent | None:
        try:
            logger.info(f"Fetching event with ID {event_id}")
            with self.session_maker() as session:
                event = session.get(KambiEvent, event_id)
                return event
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise e
    
    def get_bet_offers_for_event(self, event_id: int) -> list[BetOffer]:
        try:
            logger.info(f"Fetching bet offers for event ID {event_id}")
            with self.session_maker() as session:
                query = select(BetOffer).where(BetOffer.eventId == event_id)
                bet_offers = list(session.execute(query).scalars().all())
                return bet_offers
        except Exception as e:
            logger.error(f"Error getting bet offers for event {event_id}: {e}")
            raise e
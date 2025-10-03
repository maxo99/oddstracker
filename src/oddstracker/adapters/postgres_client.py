import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from oddstracker import config
from oddstracker.domain.kambi_event import KambiEvent

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

    def add_event(self, event: KambiEvent):
        try:
            logger.info(f"Upserting event {event.id}.")
            with self.session_maker() as session:
                session.add(event)
                logger.info(f"Upserted event {event.id} successfully.")
                session.commit()
        except Exception as e:
            logger.error(f"Error upserting events: {e}")
            raise e

    # def upsert_events(self, events: list[Event], allow_reset: bool = False):
    #     try:
    #         logger.info(f"Upserting {len(events)} events.")
    #         with self.session_maker() as session:
    #             updated_events = []
    #             for event in events:
    #                 existing_event = session.get(Event, event.id)
    #                 if existing_event:
    #                     for key, value in event.model_dump().items():
    #                         if hasattr(event, key) and "vector" in key:
    #                             # Handle vector fields specifically
    #                             vector_value = getattr(event, key)
    #                             if allow_reset or (
    #                                 vector_value is not None and len(vector_value) > 0
    #                             ):
    #                                 setattr(existing_event, key, vector_value)
    #                         else:
    #                             # Handle non-vector fields
    #                             if allow_reset or (value is not None and value != ""):
    #                                 setattr(existing_event, key, value)
    #                     updated_events.append(existing_event)
    #                 else:
    #                     session.add(event)
    #                     updated_events.append(event)
    #             session.commit()
    #             # Only refresh the events that are actually in this session
    #             if updated_events:
    #                 logger.info(f"Refreshing {len(updated_events)} events in session.")
    #             for event in updated_events:
    #                 session.refresh(event)
    #         logger.info(f"Upserted {len(updated_events)} events successfully.")
    #     except Exception as e:
    #         logger.error(f"Error upserting events: {e}")
    #         raise e

    # def get_events(self, **filters) -> list[Event]:
    #     try:
    #         logger.info(f"Fetching events from with {filters}")
    #         query = select(Event)
    #         with self.session_maker() as session:
    #             query = select(Event)
    #             if filters:
    #                 for key, value in filters.items():
    #                     if key.startswith("not_"):
    #                         # Handle "not equal" filters
    #                         actual_key = key[4:]  # Remove "not_" prefix
    #                         query = query.where(getattr(Event, actual_key) != value)
    #                     else:
    #                         # Handle regular equality filters
    #                         query = query.where(getattr(Event, key) == value)
    #             return list(session.execute(query).scalars().all())
    #     except Exception as e:
    #         logger.error(f"Error getting events: {e}")
    #         raise e

    # def get_event_by_id(self, event_id: str) -> Event | None:
    #     try:
    #         with self.session_maker() as session:
    #             return session.get(Event, event_id) or None
    #     except Exception as e:
    #         raise e

    # def get_count(self, **filters) -> int:
    #     try:
    #         with self.session_maker() as session:
    #             query = select(func.count(cast(Event.id, sqlmodel.String)))
    #             if filters:
    #                 for key, value in filters.items():
    #                     if key.startswith("not_"):
    #                         actual_key = key[4:]
    #                         query = query.where(getattr(Event, actual_key) != value)
    #                     else:
    #                         query = query.where(getattr(Event, key) == value)
    #             result = session.execute(query).scalar_one()
    #             return result
    #     except Exception as e:
    #         logger.error(f"Error getting event count: {e}")
    #         raise e

    # def delete_event(self, event_id: str):
    #     try:
    #         with self.session_maker() as session:
    #             event = session.get(Event, event_id)
    #             if event:
    #                 session.delete(event)
    #                 session.commit()
    #             else:
    #                 raise ValueError(f"Event with id {event_id} not found")
    #     except Exception as e:
    #         raise e

    # def search_by_title_embeddings(
    #     self,
    #     title_embedding: list[float],
    #     event_exclusion_id: str | None = None,
    #     limit: int = 5,
    #     similarity_threshold: float = 0.999,
    # ) -> SimilarityResponse:
    #     try:
    #         logger.info("Searching events by title embedding")
    #         embedding_sql = self._format_embedding(title_embedding)

    #         with self.session_maker() as session:
    #             dist = func.cosine_distance(Event.title_vector, embedding_sql)

    #             query = select(Event, dist.label("cosine_distance")).where(
    #                 dist < similarity_threshold
    #             )
    #             if event_exclusion_id is not None:
    #                 query = query.where(not_(Event.id == event_exclusion_id))
    #             results = session.execute(query.order_by(dist).limit(limit)).all()

    #             logger.info(f"Found {len(results)} events matching title embedding")
    #             return SimilarityResponse(
    #                 events=[r[0] for r in results], scores=[1.0 - r[1] for r in results]
    #             )
    #     except Exception as e:
    #         logger.error(f"Error searching events by title: {e}")
    #         raise e

    # def search_by_qualifications_embeddings(
    #     self,
    #     qe: list[float] | ndarray,
    #     event_exclusion_id: str | None = None,
    #     limit: int = 5,
    #     similarity_threshold: float = 0.999,
    # ) -> SimilarityResponse:
    #     try:
    #         logger.info("Searching events by qualifications embedding")
    #         embedding_sql = self._format_embedding(qe)

    #         with self.session_maker() as session:
    #             dist = func.cosine_distance(Event.qualifications_vector, embedding_sql)
    #             query = select(Event, dist.label("cosine_distance")).where(
    #                 dist < similarity_threshold
    #             )
    #             if event_exclusion_id is not None:
    #                 query = query.where(not_(Event.id == event_exclusion_id))
    #             results = session.execute(query.order_by(dist).limit(limit)).all()
    #             logger.info(f"Found {len(results)} events similar events")
    #             return SimilarityResponse(
    #                 events=[r[0] for r in results], scores=[1.0 - r[1] for r in results]
    #             )
    #     except Exception as e:
    #         logger.error(f"Error searching events by qualifications: {e}")
    #         raise e

    # @staticmethod
    # def _format_embedding(embedding: list[float] | ndarray) -> TextClause:
    #     """Format the embedding for SQL query."""
    #     if isinstance(embedding, ndarray):
    #         embedding = embedding.tolist()
    #     _embedding_str = ",".join([f"{float(x):.10f}" for x in embedding])
    #     return text(f"ARRAY[{_embedding_str}]::vector")

    # def search_by_combined_criteria(
    #     self,
    #     title_embedding: list[float] | None = None,
    #     qualifications_embedding: list[float] | None = None,
    #     title_weight: float = 0.4,
    #     qualifications_weight: float = 0.6,
    #     limit: int = 5,
    #     similarity_threshold: float = 0.7
    # ) -> list[Event]:
    #     try:
    #         logger.info("Searching events by combined title and qualifications embeddings")

    #         with self.session_maker() as session:
    #             query = session.query(Event)

    #             # Build distance calculation based on available embeddings
    #             distance_expressions = []

    #             if title_embedding and qualifications_embedding:
    #                 title_str = str(title_embedding).replace("[", "").replace("]", "")
    #                 qual_str = str(qualifications_embedding).replace("[", "").replace("]", "")
    #                 title_sql = text(f"ARRAY[{title_str}]::vector")
    #                 qual_sql = text(f"ARRAY[{qual_str}]::vector")

    #                 combined_distance = (
    #                     title_weight * func.cosine_distance(Event.title_vector, title_sql) +
    #                     qualifications_weight * func.cosine_distance(Event.qualifications_vector, qual_sql)
    #                 )
    #                 query = query.filter(
    #                     Event.title_vector.isnot(None),
    #                     Event.qualifications_vector.isnot(None)
    #                 )

    #             elif title_embedding:
    #                 title_str = str(title_embedding).replace("[", "").replace("]", "")
    #                 title_sql = text(f"ARRAY[{title_str}]::vector")
    #                 combined_distance = func.cosine_distance(Event.title_vector, title_sql)
    #                 query = query.filter(Event.title_vector.isnot(None))

    #             elif qualifications_embedding:
    #                 qual_str = str(qualifications_embedding).replace("[", "").replace("]", "")
    #                 qual_sql = text(f"ARRAY[{qual_str}]::vector")
    #                 combined_distance = func.cosine_distance(Event.qualifications_vector, qual_sql)
    #                 query = query.filter(Event.qualifications_vector.isnot(None))

    #             else:
    #                 raise ValueError("At least one embedding must be provided")

    #             results = (
    #                 query
    #                 .filter(combined_distance < similarity_threshold)
    #                 .order_by(combined_distance)
    #                 .limit(limit)
    #                 .all()
    #             )

    #             logger.info(f"Found {len(results)} events matching combined criteria")
    #             return results
    #     except Exception as e:
    #         logger.error(f"Error searching events by combined criteria: {e}")
    #         raise e

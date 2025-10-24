import logging
import os

from dotenv import load_dotenv

load_dotenv()

if root_from_env := os.getenv("ROOT_DIR"):
    ROOT_DIR = root_from_env
else:
    import git

    ROOT_DIR = str(git.Repo(".", search_parent_directories=True).working_tree_dir)

load_dotenv(ROOT_DIR)

DATA_DIR = os.getenv("DATA_DIR", os.path.join(ROOT_DIR, "data"))
APP_PORT = int(os.getenv("APP_PORT", 8080))

## Logging settings

LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())
logging.basicConfig(level=LOG_LEVEL)


# PostgreSQL settings


POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5444")
POSTGRES_DB = os.getenv("POSTGRES_DB", "oddstracker")

TOA_API_KEY = os.environ.get("THEODDSAPI_KEY")


def get_pg_url(db: str | None = None) -> str:
    db = db or POSTGRES_DB
    return (
        f"postgresql://{POSTGRES_USER}:"
        f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{db}"
    )

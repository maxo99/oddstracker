import os

import git

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "jobfinder")
CHAT_MODE = os.getenv("CHAT_MODE", "ollama").lower()
EMBEDDINGS_ENABLED = os.getenv("EMBEDDINGS_ENABLED", "true").lower() == "true"

ROOT_DIR = str(git.Repo(".", search_parent_directories=True).working_tree_dir)
DATA_DIR = os.path.join(ROOT_DIR, "data")

def get_pg_url(db: str | None = None) -> str:
    db = db or POSTGRES_DB
    return (
        f"postgresql://{POSTGRES_USER}:"
        f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{db}"
    )

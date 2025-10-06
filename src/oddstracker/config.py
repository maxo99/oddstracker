import os

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5444")
POSTGRES_DB = os.getenv("POSTGRES_DB", "oddstracker")

if root_from_env := os.getenv("ROOT_DIR"):
    ROOT_DIR = root_from_env
else:
    import git
    ROOT_DIR = str(git.Repo(".", search_parent_directories=True).working_tree_dir)

DATA_DIR = os.path.join(ROOT_DIR, "data")


APP_PORT = int(os.getenv("APP_PORT", 8000))

def get_pg_url(db: str | None = None) -> str:
    db = db or POSTGRES_DB
    return (
        f"postgresql://{POSTGRES_USER}:"
        f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{db}"
    )

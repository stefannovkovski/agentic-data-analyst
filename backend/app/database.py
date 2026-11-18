"""Connection to the data source the agents analyse."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine, inspect, text


@lru_cache
def get_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def check_connection(engine: Engine) -> dict:
    """Ask the database who we are and which version it runs."""
    with engine.connect() as conn:
        user, version = conn.execute(text("SELECT current_user, version()")).one()
    return {"user": user, "version": version.split(",")[0]}


def list_tables(engine: Engine) -> list[dict]:
    """List every table and its column names."""
    inspector = inspect(engine)
    return [
        {"table": name, "columns": [c["name"] for c in inspector.get_columns(name)]}
        for name in inspector.get_table_names()
    ]
"""The HTTP API. It stays thin: it only connects requests to the rest of the code."""

from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import check_connection, get_engine, list_tables

app = FastAPI(title="Agentic Data Analyst", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Is the API itself running?"""
    return {"status": "ok"}


@app.get("/api/datasource")
def datasource() -> dict:
    """Can we reach the database, and which tables does it have?"""
    engine = get_engine(get_settings().data_source_url)
    try:
        return {"connection": check_connection(engine), "tables": list_tables(engine)}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach the database: {e}") from e

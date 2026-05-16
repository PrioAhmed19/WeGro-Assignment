from functools import lru_cache
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import get_settings


@lru_cache()
def get_engine() -> Engine:
    """Create a cached SQLAlchemy engine for the agriculture MySQL database."""
    settings = get_settings()
    password = quote_plus(settings.PASSWORD)
    database_url = (
        f"mysql+pymysql://{settings.USER}:{password}"
        f"@{settings.HOST}:{settings.PORT}/{settings.DB}"
    )
    return create_engine(database_url, pool_pre_ping=True)

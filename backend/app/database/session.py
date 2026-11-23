import ssl
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def database_connect_args() -> dict:
    if settings.database_ssl:
        return {"ssl_context": ssl.create_default_context()}
    return {}


engine = create_engine(
    settings.database_url,
    connect_args=database_connect_args(),
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session

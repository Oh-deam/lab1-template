import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def get_database_url() -> str:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://program:test@localhost:5432/persons",
    )

    if url.startswith("postgresql://"):
        return url.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1,
        )

    if url.startswith("postgres://"):
        return url.replace(
            "postgres://",
            "postgresql+psycopg2://",
            1,
        )

    return url


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
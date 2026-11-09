"""Общая конфигурация синхронного PostgreSQL-драйвера для API и Alembic."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def normalize_database_url(url: str | None) -> str:
    """Привести старый PostgreSQL URL к явно установленному psycopg2.

    SQLAlchemy 2.1 может выбирать psycopg (v3) для postgresql://,
    хотя requirements.txt устанавливает только psycopg2-binary.
    """
    if not url:
        raise ValueError("DATABASE_URL is required (postgresql+psycopg2://...)")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    if url.startswith("postgresql+psycopg2://"):
        return url
    raise ValueError("DATABASE_URL must use postgresql:// or postgresql+psycopg2://")


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL"))
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

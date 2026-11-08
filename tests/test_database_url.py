"""Регрессии совместимости URL для установленного драйвера psycopg2."""

import pytest

from app.database import normalize_database_url


@pytest.mark.parametrize(
    ("provided", "expected"),
    [
        (
            "postgresql://user:secret@db:5432/org_db_test",
            "postgresql+psycopg2://user:secret@db:5432/org_db_test",
        ),
        (
            "postgresql+psycopg2://user:secret@db:5432/org_db_test",
            "postgresql+psycopg2://user:secret@db:5432/org_db_test",
        ),
    ],
)
def test_normalize_database_url(provided, expected):
    assert normalize_database_url(provided) == expected


@pytest.mark.parametrize("provided", [None, "", "   "])
def test_database_url_required(provided):
    with pytest.raises(ValueError, match="DATABASE_URL"):
        normalize_database_url(provided)


@pytest.mark.parametrize("provided", ["sqlite:///demo.db", "postgresql+psycopg://user@db/example"])
def test_database_url_rejects_unsupported_driver(provided):
    with pytest.raises(ValueError, match="postgresql"):
        normalize_database_url(provided)

"""Negative and positive safety checks without connecting to PostgreSQL."""

import pytest

from tests.db_safety import CONFIRMATION, require_disposable_database


def test_only_disposable_local_database_is_accepted():
    require_disposable_database(
        "postgresql+psycopg2://user:password@db:5432/org_db_test",
        CONFIRMATION,
    )


@pytest.mark.parametrize(
    ("url", "confirmation"),
    [
        ("postgresql+psycopg2://u:p@db/org_db_test", None),
        ("postgresql+psycopg2://u:p@db/org_db_test", ""),
        ("postgresql+psycopg2://u:p@db/org_db_test", "1"),
        ("postgresql+psycopg2://u:p@db/org_db", CONFIRMATION),
        ("postgresql+psycopg2://u:p@db/production_test", CONFIRMATION),
        ("postgresql+psycopg2://u:p@remote.example.com/org_db_test", CONFIRMATION),
        ("postgresql+psycopg://u:p@db/org_db_test", CONFIRMATION),
        ("sqlite:///org_db_test", CONFIRMATION),
    ],
)
def test_destructive_guard_rejects_unsafe_configurations(url, confirmation):
    with pytest.raises(RuntimeError, match="Destructive tests"):
        require_disposable_database(url, confirmation)

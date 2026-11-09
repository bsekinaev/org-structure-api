"""Guard for destructive integration test setup; never used by the application."""

from sqlalchemy.engine import make_url

CONFIRMATION = "YES_DELETE_ORG_DB_TEST"


def require_disposable_database(test_url: str, confirmation: str | None) -> None:
    """Reject DB deletion unless explicitly targeting a disposable local DB."""
    if confirmation != CONFIRMATION:
        raise RuntimeError("Destructive tests require ALLOW_DESTRUCTIVE_TEST_DB=" + CONFIRMATION)

    url = make_url(test_url)
    if (
        url.drivername != "postgresql+psycopg2"
        or url.database != "org_db_test"
        or url.host not in {"db", "localhost", "127.0.0.1"}
    ):
        raise RuntimeError(
            "Destructive tests may only reset org_db_test on local/Compose PostgreSQL"
        )

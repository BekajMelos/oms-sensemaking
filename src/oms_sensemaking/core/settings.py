import logging

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.settings import Setting
from oms_sensemaking.runtime_settings import RUNTIME_SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


def fetch_settings_from_db() -> dict[str, str]:
    """Fetch all persisted settings from the database."""
    with db_session() as db:
        rows = db.query(Setting).all()
        return {row.field_name: row.field_value for row in rows}


def load_runtime_settings_from_db() -> None:
    """Load settings from the database with the RuntimeSettings bulk_set() call"""
    db_settings = fetch_settings_from_db()
    if not db_settings:
        LOGGER.info("No runtime settings found in DB")
        return

    LOGGER.info("Applying runtime settings from DB: %s", db_settings)
    RUNTIME_SETTINGS.bulk_set(db_settings)

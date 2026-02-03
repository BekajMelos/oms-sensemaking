import logging

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.core.events import LISTENERS
from oms_sensemaking.core.runtime_settings import RUNTIME_SETTINGS
from oms_sensemaking.models.settings import Setting

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


def _handle_runtime_setting_change(key: str, value: int) -> None:
    """Helper for /settings endpoint to apply runtime settings reactions"""
    if key == "rabbitmq_prefetch_count":
        for listener in LISTENERS:
            try:
                listener.update_prefetch(value)
            except Exception:
                LOGGER.exception("Failed to update prefetch on listener %s", listener)


def apply_settings_updates(updates):
    """Iterate through settings updates and apply to runtime settings"""
    for key, value in updates.items():
        RUNTIME_SETTINGS.set(key, value)  # state
        _handle_runtime_setting_change(key, value)  # reaction

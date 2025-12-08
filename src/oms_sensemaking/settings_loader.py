import logging

from oms_sensemaking.api.routers.settings import _fetch_settings_from_db
from oms_sensemaking.config import Settings

LOGGER = logging.getLogger(__name__)


def load_settings_with_db_override(base_settings: Settings) -> Settings:
    """
    Load settings from the DB and merge them over
    the current active Settings (DB wins).
    """
    try:
        db_settings = _fetch_settings_from_db()
        LOGGER.info("Loaded %d DB settings", len(db_settings))
    except Exception as e:
        LOGGER.warning(
            "Failed to load DB settings, using existing settings: %s",
            e,
        )
        db_settings = {}

    for key, value in db_settings.items():
        if key in base_settings.model_fields:
            setattr(base_settings, key, value)

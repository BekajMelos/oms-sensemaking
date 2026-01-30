"""Rest Endpoints for Settings Management"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.api.schemas.settings import SettingsBatchUpdate, SettingUpdate
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.core.events import LISTENERS
from oms_sensemaking.models.settings import Setting
from oms_sensemaking.runtime_settings import RUNTIME_SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.post("/settings", status_code=201)
def create_or_update_setting(
    setting: SettingUpdate, user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]
) -> Response:
    """Create or update a single setting."""
    LOGGER.info("Updating setting %s", setting.field_name)
    with db_session() as db:
        existing_setting = db.query(Setting).filter(Setting.field_name == setting.field_name).first()
        if existing_setting:
            existing_setting.field_value = setting.field_value
        else:
            new_setting = Setting(field_name=setting.field_name, field_value=setting.field_value)
            db.add(new_setting)
        db.commit()

    return Response(status_code=201)


@router.post("/settings/batch", status_code=201)
def create_or_update_settings(
    settings_update: SettingsBatchUpdate, user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]
) -> Response:
    """Create or update multiple settings at once."""
    LOGGER.info("Updating %d settings", len(settings_update.settings))

    if not settings_update.settings:
        LOGGER.info("No settings to update, skipping database operations")
        return Response(status_code=201)

    with db_session() as db:
        for field_name, field_value in settings_update.settings.items():
            existing_setting = db.query(Setting).filter(Setting.field_name == field_name).first()
            if existing_setting:
                existing_setting.field_value = field_value
            else:
                new_setting = Setting(field_name=field_name, field_value=field_value)
                db.add(new_setting)
        db.commit()

    for k, v in settings_update.settings.items():
        RUNTIME_SETTINGS.set(k, int(v))

    if "rabbitmq_prefetch_count" in settings_update.settings:
        new_val = int(settings_update.settings["rabbitmq_prefetch_count"])
        for listener in LISTENERS:
            listener.update_prefetch(new_val)

    return Response(status_code=201)


def _fetch_settings_from_db() -> dict[str, str]:
    """Fetch all persisted settings from the database."""
    with db_session() as db:
        rows = db.query(Setting).all()
        return {row.field_name: row.field_value for row in rows}


@router.get("/settings", response_model=dict[str, Any])
def get_settings(user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]) -> dict[str, str]:
    return _fetch_settings_from_db()

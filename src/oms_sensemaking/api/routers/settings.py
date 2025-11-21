"""Rest Endpoints for Settings Management"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response

import oms_sensemaking.service as service_module
from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.api.schemas.settings import SettingsBatchUpdate, SettingUpdate
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.settings import Setting

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

    # Trigger live reload
    service_module.reload_settings_and_restart_controllers()

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

    # Trigger live reload
    service_module.reload_settings_and_restart_controllers()

    return Response(status_code=201)

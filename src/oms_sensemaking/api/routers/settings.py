"""Rest Endpoints for Settings Management"""

import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.settings import Setting

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


class SettingUpdate(BaseModel):
    """Model for updating a setting."""

    field_name: str
    field_value: Any


class SettingsUpdate(BaseModel):
    """Model for updating multiple settings."""

    settings: Dict[str, Any]


@router.post("/settings", status_code=201)
def create_or_update_setting(
    setting: SettingUpdate, user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]
) -> Response:
    """Create or update a single setting."""
    LOGGER.info("Updating setting %s by user %s", setting.field_name, user_dn)
    with db_session() as db:
        existing_setting = db.query(Setting).filter(Setting.field_name == setting.field_name).first()
        if existing_setting:
            existing_setting.field_value = setting.field_value
        else:
            new_setting = Setting(field_name=setting.field_name, field_value=setting.field_value)
            db.add(new_setting)
        db.commit()

    # Trigger live reload
    _reload_settings_and_restart_controllers()

    return Response(status_code=201)


@router.post("/settings/batch", status_code=201)
def create_or_update_settings(
    settings_update: SettingsUpdate, user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]
) -> Response:
    """Create or update multiple settings at once."""
    LOGGER.info("Updating %d settings by user %s", len(settings_update.settings), user_dn)
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
    _reload_settings_and_restart_controllers()

    return Response(status_code=201)


def _reload_settings_and_restart_controllers() -> None:
    """Reload settings from database and restart controllers."""
    # Import here to avoid circular dependency
    import oms_sensemaking.service as service_module

    service_module.reload_settings_and_restart_controllers()

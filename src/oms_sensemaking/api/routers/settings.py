"""Rest Endpoints for Settings Management"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError

import oms_sensemaking.service as service_module
from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.api.schemas.setting_input_schema import SettingInputSchema
from oms_sensemaking.api.schemas.settings import SettingsUpdate, SettingUpdate
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.settings import Setting

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.post("/settings", status_code=201)
def create_or_update_setting(
    setting: SettingUpdate, user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]
) -> Response:
    """Create or update a single setting."""
    # Validate the setting using SettingInputSchema
    try:
        validated_setting = SettingInputSchema(
            field_name=setting.field_name,
            field_value=setting.field_value,
        )
    except ValidationError as e:
        LOGGER.error("Invalid setting validation: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid setting '{setting.field_name}': {str(e)}") from e

    LOGGER.info("Updating setting %s", validated_setting.field_name)
    with db_session() as db:
        existing_setting = db.query(Setting).filter(Setting.field_name == validated_setting.field_name).first()
        if existing_setting:
            existing_setting.field_value = validated_setting.field_value
        else:
            new_setting = Setting(field_name=validated_setting.field_name, field_value=validated_setting.field_value)
            db.add(new_setting)
        db.commit()

    # Trigger live reload
    service_module.reload_settings_and_restart_controllers()

    return Response(status_code=201)


@router.post("/settings/batch", status_code=201)
def create_or_update_settings(
    settings_update: SettingsUpdate, user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]
) -> Response:
    """Create or update multiple settings at once."""
    # Validate all settings before processing
    validated_settings = {}
    validation_errors = []

    for field_name, field_value in settings_update.settings.items():
        try:
            validated_setting = SettingInputSchema(
                field_name=field_name,
                field_value=field_value,
            )
            validated_settings[field_name] = validated_setting.field_value
        except ValidationError as e:
            validation_errors.append(f"'{field_name}': {str(e)}")
            LOGGER.error("Invalid setting validation for %s: %s", field_name, e)

    if validation_errors:
        raise HTTPException(status_code=400, detail=f"Invalid settings: {', '.join(validation_errors)}")

    LOGGER.info("Updating %d settings", len(validated_settings))
    with db_session() as db:
        for field_name, field_value in validated_settings.items():
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

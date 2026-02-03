"""Rest Endpoints for Settings Management"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.api.schemas.settings import SettingsBatchUpdate
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.core.settings import apply_settings_updates, fetch_settings_from_db
from oms_sensemaking.models.settings import Setting

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.patch("/settings", status_code=204)
def update_settings(settings_update: SettingsBatchUpdate, user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]):
    """Update runtime settings in batch."""
    LOGGER.info("Updating %d settings: %s", len(settings_update.settings), settings_update.settings)

    if not settings_update.settings:
        LOGGER.info("No values in Settings update request")
        return

    with db_session() as db:
        for field_name, field_value in settings_update.settings.items():
            existing_setting = db.query(Setting).filter(Setting.field_name == field_name).first()
            if existing_setting:
                existing_setting.field_value = field_value
            else:
                new_setting = Setting(field_name=field_name, field_value=field_value)
                db.add(new_setting)
        db.commit()

    updates = {key: int(value) for key, value in settings_update.settings.items()}
    apply_settings_updates(updates)

    return


@router.get("/settings", response_model=dict[str, Any])
def get_settings(user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]) -> dict[str, str]:
    return fetch_settings_from_db()

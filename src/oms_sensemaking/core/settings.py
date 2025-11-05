from typing import Any, Dict

from sqlalchemy import select

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.settings import Setting


class Settings:
    def get_settings(self) -> Dict[str, Any]:
        """
        Fetches all settings records from the database and returns them
        as a single dictionary mapping field_name to field_value.

        Assumes field_value is stored as a JSON/JSONB type, which SQLAlchemy
        automatically converts back to native Python types (dict, list, int, bool).

        Returns:
            A dictionary mapping setting name (str) to its value (Any).
        """
        with db_session() as db:
            stmt = select(Setting)

            # Execute the statement and fetch all results
            settings_results = db.execute(stmt).scalars().all()
            settings_map: Dict[str, Any] = {}
            for setting in settings_results:
                settings_map[setting.field_name] = setting.field_value

            return settings_map

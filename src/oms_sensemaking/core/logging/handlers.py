"""Module for custom logging handlers"""

import logging
from datetime import datetime, timezone

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.logs import LogRecord


# Custom handler
class DatabaseHandler(logging.Handler):
    def emit(self, record):

        if record.levelno > logging.INFO:

            log_record = LogRecord(
                level=record.levelname,
                timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc),  # is this timezone necessarily correct?
                module_name=record.name,
                message=record.message,
                exc_text=record.exc_text,
                acm={}  #  TODO No bueno
            )

            with db_session() as db:
                db.add(log_record)
                db.commit()

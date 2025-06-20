"""Module for custom logging handlers"""

import logging
import traceback
from datetime import datetime, timezone

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.logs import LogRecord


# Custom handler
class DatabaseHandler(logging.Handler):
    def emit(self, record):

        print('this is the handler\n\n\n')

        if record.levelno > logging.INFO:
            print(record)

            log_record = LogRecord(
                level=record.levelname,
                timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc),  # is this timezone necessarily correct?
                module_name=record.name,
                message=record.message,
                exc_text=record.exc_text,
                acm={}  #  TODO No bueno
            )

            # try:
            with db_session() as db:
                print("Actually writing to ", db.bind.url)

                db.add(log_record)
                db.commit()
            # except Exception:
            #     print(f"Error logging to database: {traceback.format_exc()} ")

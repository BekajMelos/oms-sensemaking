"""Module for custom logging handlers"""

import logging
import traceback
from datetime import datetime, timezone

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.logs import LogRecord

LOGGER = logging.getLogger(__name__)


DATETIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"


class DatabaseHandler(logging.Handler):
    """Custom handler to log error messages to the database"""
    def emit(self, record) -> None:
        """
        Capture log records and write error logs to the database

        :param record: Captured Log Record
        :return: None
        """

        if record.levelno > logging.INFO:

            import pprint
            pprint.pprint(record.__dict__)

            timestamp = datetime.strptime(record.asctime, DATETIME_FORMAT_STRING)
            timestamp = timestamp.astimezone(timezone.utc)

            try:
                log_record = LogRecord(
                    level=record.levelname,
                    timestamp=timestamp,
                    module_name=record.name,
                    message=record.message,
                    exc_text=record.exc_text,
                    acm={}
                )
                # id, object type, action type, audit log info
                # potentially look at call stack to find audit log info

                # TODO No bueno.
                # set a highest classification in config and use that?
                # calc based on highest classification in the db?
                # maybe only exceptions? and/or maybe only the traceback?
                # does the table need a classification if not publicly accessible?
                # if we use the logger "correctly", we can get these
                # `LOGGER.error("Error encountered while processing %s from buffer: %s", track_uuid, str(e))`

                with db_session() as db:
                    db.add(log_record)
                    db.commit()
            except Exception:
                LOGGER.debug(f"Error encountered while logging to database: {traceback.format_exc()} ")

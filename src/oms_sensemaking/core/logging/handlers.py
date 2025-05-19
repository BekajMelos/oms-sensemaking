"""Module for custom logging handlers"""

import logging
from datetime import datetime, timezone

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.models.logs import LogRecord


# Custom handler
class DatabaseHandler(logging.Handler):
    def emit(self, record):

        # TODO doing it this way, I don't know if we can still print the log messages to the log like normal
        # call super?

        # try:
        if record.levelno > logging.INFO:

            # print(record.filename)     # controllers.py
            # print(record.funcName)     # flush_buffer
            # print(record.module)       # controllers
            # print(record.pathname)     # /app/src/oms_sensemaking/geospatial/controllers.py
            # print(record.process)      # 1176
            # print(record.processName)  # SpawnProcess-11
            # print(record.name)         # oms_sensemaking.geospatial.controllers
            # print(record.thread)       #  281472470675840
            # print(record.threadName)   #  Thread-16
            # print("message: ", record.message)
            # print("exc_info: ", record.exc_info)
            # print("exc_text: ", record.exc_text)
            # print("stack_info: ", record.stack_info)
            # message:  Error encountered while processing 922ba3f9-01e7-42b3-acd7-22705de3e320 from buffer
            # exc_info:  (<class 'UnboundLocalError'>, UnboundLocalError("cannot access local variable 'track' where it is not associated with a value"), <traceback object at 0xffff839204c0>)
            # exc_text:  Traceback (most recent call last):
            #     File "/app/src/oms_sensemaking/geospatial/controllers.py", line 276, in flush_buffer
            #     node = self.oms_crud_tool.get_node(track.node_id)
            #                                            ^^^^^
            #      UnboundLocalError: cannot access local variable 'track' where it is not associated with a value
            # stack_info:  None
            # LogRecord(created_at=None, acm={}, log_id=None, timestamp=datetime.datetime(2025, 6, 2, 21, 37, 14, 991362, tzinfo=datetime.timezone.utc), level='ERROR', thread_name='oms_sensemaking.geospatial.controllers', message='Error encountered while processing %s from buffer')

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

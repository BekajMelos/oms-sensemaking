"""Test DB Logging"""
import json
import logging
import time
from datetime import datetime, timezone
import uuid

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from oms_sensemaking.config import LogConfig, SETTINGS
from oms_sensemaking.core.logging.handlers import DatabaseHandler
from oms_sensemaking.models.logs import LogLevel, LogRecord


LOGGER = logging.getLogger(__name__)

formatter = LogConfig().formatters["custom"]
handler = DatabaseHandler()
handler.setFormatter(formatter)

LOGGER.addHandler(DatabaseHandler())


def test_db_logging(db: Session):
    """Test that errors are logged to DB"""

    print(db.bind.url)
    print("count logrecord: ", db.execute(select(LogRecord)).scalars().all())

    start_time = datetime.now(tz=timezone.utc)

    # check that cotravels exist in Findings table
    logs = (
        db.execute(delete(LogRecord))
    )

    queue_name = SETTINGS.rmq_geo_queue_name
    credentials = PlainCredentials(SETTINGS.rabbitmq_username, SETTINGS.rabbitmq_password)
    parameters = ConnectionParameters(
        host="localhost",
        port=SETTINGS.rabbitmq_port,
        virtual_host=SETTINGS.rabbitmq_vhost,
        credentials=credentials,
    )
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(
        queue=queue_name, durable=True, arguments={"x-delivery-limit": -1, "x-queue-type": "quorum"}
    )
    channel.basic_publish(exchange='', routing_key=queue_name, body='Hello World!')
    connection.close()


    for _ in range(3):
        # check that cotravels exist in Findings table
        logs = (
            db.execute(select(LogRecord).filter(LogRecord.level == LogLevel.ERROR).order_by(desc(LogRecord.created_at)))
            .scalars()
            .all()
        )
        if logs and logs[0].created_at > start_time:
            break
        time.sleep(1)

    assert len(logs) == 1
    log = logs[0]
    assert log.message
    assert "JSONDecodeError" in log.message
    assert log.module_name == "oms_sensemaking.core.events"
    assert False, 'it succeeded'



def test_db_logging_within_sensemaker(db: Session):
    """Test that errors are logged to DB"""
    print(db.bind.url)
    print("count logrecord: ", db.execute(select(LogRecord)).scalars().all())

    start_time = datetime.now(tz=timezone.utc)

    # check that cotravels exist in Findings table
    db.execute(delete(LogRecord))

    queue_name = SETTINGS.mil_symbol_settings.rmq_mil_symbol_queue_name
    credentials = PlainCredentials(SETTINGS.rabbitmq_username, SETTINGS.rabbitmq_password)
    parameters = ConnectionParameters(
        host="localhost",
        port=SETTINGS.rabbitmq_port,
        virtual_host=SETTINGS.rabbitmq_vhost,
        credentials=credentials,
    )
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(
        queue=queue_name, durable=True, arguments={"x-delivery-limit": -1, "x-queue-type": "quorum"}
    )

    body = {
        "objectId": str(uuid.uuid4()),
        "userId": "user",
        "objectType": "NODE",
        "action": "CREATE"
    }

    channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(body))
    connection.close()


    for _ in range(3):
        # check that cotravels exist in Findings table
        logs = (
            db.execute(select(LogRecord).filter(LogRecord.level == LogLevel.WARNING).order_by(desc(LogRecord.created_at)))
            .scalars()
            .all()
        )
        if logs and logs[0].created_at > start_time:
            break
        time.sleep(1)

    assert len(logs) == 1
    log = logs[0]
    assert log.message
    assert "Could not find" in log.message
    assert log.module_name == "oms_sensemaking.core.controllers"

    assert False, 'it succeeded'
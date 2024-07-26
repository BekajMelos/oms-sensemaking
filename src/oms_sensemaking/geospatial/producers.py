"""Provides "producers" useful for working with the oms_sensemaking algorithms."""
import asyncio
import logging
from datetime import datetime, timezone

import pandas as pd

from oms_sensemaking.geospatial.track_cache import Attribute

LOGGER: logging.Logger = logging.getLogger(__name__)


async def produce_attributes_from_csv(q: asyncio.Queue, file_name: str) -> None:
    """
    Publish CSV data to an asyncio Queue.

    :param q: The Queue to publish data to.
    :param file_name: The CSV file to parse.
    """
    LOGGER.info("Producer: Running")

    df = pd.read_csv(file_name)
    LOGGER.debug(df)
    for _, row in df.iterrows():
        point = Attribute(identifier=row["r"], lat=row["lat"], lon=row["lon"])
        point.timestamp = datetime.fromtimestamp(int(row["now"]), tz=timezone.utc)
        await q.put(point)

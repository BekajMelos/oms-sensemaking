import argparse
import asyncio
import logging
import time
from datetime import datetime, timezone
from logging.config import dictConfig

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from oms_sensemaking.config import LogConfig
from oms_sensemaking.services.track_cache import Attribute, TrackCacheService

LOGGER = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging


async def produce(q: asyncio.Queue, file_name: str) -> None:
    LOGGER.info("Producer: Running")

    df = pd.read_csv(file_name)
    LOGGER.debug(df)
    for _, row in df.iterrows():
        point = Attribute(identifier=row["r"], lat=row["lat"], lon=row["lon"])
        point.timestamp = datetime.fromtimestamp(int(row["now"]), tz=timezone.utc)
        await q.put(point)


async def main(filename: str):
    q: asyncio.Queue = asyncio.Queue()
    track_cache_service = TrackCacheService(q)

    producers = [asyncio.create_task(produce(q, filename))]
    await track_cache_service.wait_for_events()
    await asyncio.gather(*producers)
    await q.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="sub-command help")

    # create the parser for the "produce" command
    produce_parser = subparsers.add_parser("produce", help="Example producer that reads input from a file")
    produce_parser.add_argument("filename", type=str, help="File to run on.")

    start = time.perf_counter()

    try:
        asyncio.run(main(**parser.parse_args().__dict__))
    except KeyboardInterrupt:
        LOGGER.info("Exiting.")

    elapsed = time.perf_counter() - start
    LOGGER.info(f"Program completed in {elapsed:0.5f} seconds.")

import argparse
import asyncio
import logging
import os
import time
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from oms_sensemaking.services.track_cache import Attribute, TrackCacheService  # noqa: E402

DEBUG = os.environ.get("DEBUG", "false").lower() in ["true", "yes"]
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s-%(filename)s-%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(LOG_LEVEL)


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

"""Provides a CLI for oms-sensemaking."""
import asyncio
import logging
import time
from argparse import ArgumentParser, Namespace
from logging.config import dictConfig

from dotenv import load_dotenv

load_dotenv()

from oms_sensemaking.config import LogConfig
from oms_sensemaking.geospatial.producers import produce_attributes_from_csv
from oms_sensemaking.geospatial.track_cache import TrackCacheService

LOGGER = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging


async def run_geospatial(filename: str) -> None:
    """
    Run the geospatial algorithms.

    :param filename: The path to a CSV input file.
    """
    q: asyncio.Queue = asyncio.Queue()
    track_cache_service: TrackCacheService = TrackCacheService(q)

    producers: list[asyncio.Task] = [asyncio.create_task(produce_attributes_from_csv(q, filename))]
    await track_cache_service.wait_for_events()
    await asyncio.gather(*producers)
    await q.join()


def run_nlp() -> None:
    """Run the NLP algorithms."""
    raise NotImplementedError('NLP is not implemented yet')


def get_cli_parser() -> ArgumentParser:
    """Return a configured CLI argument parser."""
    parser: ArgumentParser = ArgumentParser(
        description='A utility for analysing OMS data.',
        prog='oms_sensemaking')
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description="Run 'python -m oms_sensemaking COMMAND -h' for more information.")
    subparsers.required = True

    # geospatial subcommand
    geo_parser: ArgumentParser = subparsers.add_parser("geo", help="Run geospatial analytics.")
    geo_parser.add_argument("filename", type=str, help="File to run on.")
    geo_parser.set_defaults(
        func=lambda args: asyncio.run(run_geospatial(args.filename))
    )

    # natural language processing subcommand
    nlp_parser: ArgumentParser = subparsers.add_parser("nlp", help="Run NLP analytics.")
    nlp_parser.set_defaults(
        func=lambda args: run_nlp()
    )

    return parser


def main() -> None:
    """Entry point to running the heatmapper CLI."""
    args: Namespace = get_cli_parser().parse_args()
    start: float = time.perf_counter()

    try:
        args.func(args)  # call default function for the given command
    except KeyboardInterrupt:
        LOGGER.warning("Exiting.")
        exit(0)
    except NotImplementedError as nie:
        LOGGER.warning(nie)
        exit(1)

    elapsed: float = time.perf_counter() - start
    LOGGER.info(f"Program completed in {elapsed:0.5f} seconds.")


main()

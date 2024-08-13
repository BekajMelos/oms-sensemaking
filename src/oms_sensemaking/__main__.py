"""Provides a CLI for oms-sensemaking."""
import asyncio
import logging
import time
from argparse import ArgumentParser, Namespace
from logging.config import dictConfig
from typing import Optional

import shapely
from dotenv import load_dotenv

load_dotenv()

from oms_sensemaking.config import SETTINGS, LogConfig
from oms_sensemaking.geospatial.cotravel import CotravelService
from oms_sensemaking.geospatial.geo_sqs_listener import GeoSQSListener
from oms_sensemaking.geospatial.loiter import LoiterService
from oms_sensemaking.geospatial.similar_tracks import MostSimilarTrackService
from oms_sensemaking.geospatial.tracks import TRACK_CREATED_EVENT, TrackCacheService, produce_attributes_from_csv

LOGGER = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging


async def run_geospatial(filename: Optional[str] = None, verbose: int = 0) -> None:
    """
    Run the geospatial algorithms.

    :param filename: The path to a CSV input file.
    :param verbose: A number to indicate how verbose logging should be.
    """
    q: asyncio.Queue = asyncio.Queue()
    track_cache_service: TrackCacheService = TrackCacheService(q)

    if verbose > 0:
        LOGGER.debug("Registering verbose LineString logger")
        track_cache_service.subscribe(
            TRACK_CREATED_EVENT,
            lambda track: LOGGER.debug(
                shapely.LineString([(point.geometry.x, point.geometry.y) for point in track.points])
            ),
        )

    if SETTINGS.detect_cotravels:
        LOGGER.debug('Registering "co-travel" sensemaker')
        track_cache_service.subscribe(TRACK_CREATED_EVENT, CotravelService.detect_cotravels)

    if SETTINGS.detect_loiters:
        LOGGER.debug('Registering "loiter" sensemaker')
        track_cache_service.subscribe(TRACK_CREATED_EVENT, LoiterService.detect_loiters)

    if SETTINGS.similar_tracks:
        LOGGER.debug('Registering "similar tracks" sensemaker')
        track_cache_service.subscribe(TRACK_CREATED_EVENT, MostSimilarTrackService.most_similar_track_node_ids)

    if filename:
        task = asyncio.create_task(produce_attributes_from_csv(q, filename))
    else:
        sqs_listener = GeoSQSListener(q)
        task = asyncio.create_task(sqs_listener.listen())

    try:
        # producers: list[asyncio.Task] = [asyncio.create_task(produce_attributes_from_csv(q, filename))]
        await track_cache_service.wait_for_events()
        await task
        await q.join()
    finally:
        LOGGER.warning("shutting down pub/sub")
        track_cache_service.stop()


def run_nlp() -> None:
    """Run the NLP algorithms."""
    raise NotImplementedError("NLP is not implemented yet")


def get_cli_parser() -> ArgumentParser:
    """Return a configured CLI argument parser."""
    parser: ArgumentParser = ArgumentParser(description="A utility for analysing OMS data.", prog="oms_sensemaking")
    parser.add_argument("-V", "--verbose", action="count", default=0, help="A flag to enable verbose logging.")

    subparsers = parser.add_subparsers(
        dest="command", title="commands", description="Run 'python -m oms_sensemaking COMMAND -h' for more information."
    )
    subparsers.required = True

    # geospatial subcommand
    geo_parser: ArgumentParser = subparsers.add_parser("geo", help="Run geospatial analytics.")
    geo_parser.add_argument("-f", "--filename", type=str, help="File to run on.")
    geo_parser.set_defaults(func=lambda args: asyncio.run(run_geospatial(args.filename, verbose=args.verbose)))

    # natural language processing subcommand
    nlp_parser: ArgumentParser = subparsers.add_parser("nlp", help="Run NLP analytics.")
    nlp_parser.set_defaults(func=lambda args: run_nlp())

    return parser


def main() -> None:
    """Entry point to running the oms_sensemaking CLI."""
    args: Namespace = get_cli_parser().parse_args()

    if args.verbose == 1:
        logging.getLogger(__package__).setLevel(logging.DEBUG)
    elif args.verbose > 1:
        root_logger: logging.Logger = logging.getLogger()

        root_logger.setLevel(logging.DEBUG)
        for handler in root_logger.handlers:
            handler.setLevel(logging.DEBUG)

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

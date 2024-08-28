"""Provides a CLI for oms-sensemaking."""
import logging
import time
from argparse import ArgumentParser, Namespace
from logging.config import dictConfig
from threading import Thread
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from oms_sdk import DEFAULT_ACM

from oms_sensemaking.config import SETTINGS, LogConfig
from oms_sensemaking.core.controllers import SensemakerController, run_controller
from oms_sensemaking.core.events import DummyObjectEventConsumer
from oms_sensemaking.geospatial.controllers import (
    CSVFileParser,
    GeospatialSensemakerController,
    GeoSQSListener,
)
from oms_sensemaking.nlp.controllers import NlpSensemakerController
from oms_sensemaking.semantic.controllers import SemanticSensemakerController

LOGGER = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging


def start_controller_and_wait(controller: SensemakerController) -> None:
    """
    Start a controller in a thread and waits for it to finish.

    This function blocks the current thread. If a ``KeyboardInterrupt`` is
    raised, the controller will be stopped.
    """
    controller_thread: Thread = Thread(target=run_controller, args=(controller,))

    try:
        controller_thread.start()
        controller_thread.join()
    except KeyboardInterrupt:
        LOGGER.warning("actually handling the keyboard stop")
        controller.stop()

        if controller_thread.is_alive():
            LOGGER.warning("Thread status: %s", controller_thread.is_alive())
            controller_thread.join()


def run_geospatial(filename: Optional[str] = None, verbose: int = 0) -> None:
    """
    Run the geospatial algorithms.

    :param filename: The path to a CSV input file.
    :param verbose: A number to indicate how verbose logging should be.
    """
    geo: GeospatialSensemakerController = GeospatialSensemakerController(
        GeoSQSListener() if filename is None else CSVFileParser(
            filename,
            DEFAULT_ACM,
            SETTINGS.user_dn
        )
    )

    start_controller_and_wait(geo)
    # if verbose > 0:
    #     # TODO: enable verbose logging
    #     # LOGGER.debug("Registering verbose LineString logger")
    #     pass

# TODO: move the logic in this bloc elsewhere
# async def run_geospatial(filename: Optional[str] = None, verbose: int = 0) -> None:
#     """
#     Run the geospatial algorithms.
#
#     :param filename: The path to a CSV input file.
#     :param verbose: A number to indicate how verbose logging should be.
#     """
#     q: asyncio.Queue = asyncio.Queue()
#     track_cache_service: TrackCacheService = TrackCacheService(q)
#
#     if verbose > 0:
#         LOGGER.debug("Registering verbose LineString logger")
#         track_cache_service.subscribe(
#             TRACK_CREATED_EVENT,
#             lambda track: LOGGER.debug(
#                 shapely.LineString([(point.geometry.x, point.geometry.y) for point in track.points])
#             ),
#         )
#
#     if SETTINGS.detect_cotravels:
#         LOGGER.debug('Registering "co-travel" sensemaker')
#         track_cache_service.subscribe(TRACK_CREATED_EVENT, CotravelService.detect_cotravels)
#
#     if SETTINGS.detect_loiters:
#         LOGGER.debug('Registering "loiter" sensemaker')
#         track_cache_service.subscribe(TRACK_CREATED_EVENT, LoiterService.detect_loiters)
#
#     if SETTINGS.similar_tracks:
#         LOGGER.debug('Registering "similar tracks" sensemaker')
#         track_cache_service.subscribe(TRACK_CREATED_EVENT, MostSimilarTrackService.most_similar_track_node_ids)
#
#     if filename:
#         task = asyncio.create_task(produce_attributes_from_csv(q, filename))
#     else:
#         sqs_listener = GeoSQSListener(q)
#         task = asyncio.create_task(sqs_listener.listen())
#
#     try:
#         await track_cache_service.wait_for_events()
#         await task
#         await q.join()
#     finally:
#         LOGGER.warning("shutting down pub/sub")
#         track_cache_service.stop()


def run_nlp() -> None:
    """Run the NLP algorithms."""
    start_controller_and_wait(NlpSensemakerController(DummyObjectEventConsumer()))


def run_semantic() -> None:
    """Run the semantic algorithms."""
    start_controller_and_wait(SemanticSensemakerController(DummyObjectEventConsumer()))


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
    geo_parser.set_defaults(func=lambda args: run_geospatial(args.filename, verbose=args.verbose))

    # natural language processing subcommand
    nlp_parser: ArgumentParser = subparsers.add_parser("nlp", help="Run NLP analytics.")
    nlp_parser.set_defaults(func=lambda args: run_nlp())

    semantic_parser: ArgumentParser = subparsers.add_parser("semantic", help="Run semantic workflow.")
    semantic_parser.set_defaults(func=lambda args: run_semantic())

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


if __name__ == "__main__":
    main()

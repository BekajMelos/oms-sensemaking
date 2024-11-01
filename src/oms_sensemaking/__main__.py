"""
Provides a CLI for oms-sensemaking.

```
$ python -m oms_sensemaking -h
usage: oms_sensemaking [-h] [-V] {geo,nlp,semantic} ...

A utility for analysing OMS data.

options:
  -h, --help          show this help message and exit
  -V, --verbose       A flag to enable verbose logging.

commands:
  Run 'python -m oms_sensemaking COMMAND -h' for more information.

  {geo,nlp,semantic}
    geo               Run geospatial analytics.
    nlp               Run NLP analytics.
    semantic          Run semantic workflow.
```

Geospatial CLI
==============

Run the geospatial algorithms.

```
$ python -m oms_sensemaking geo -h
usage: oms_sensemaking geo [-h] [-H DB_HOST] [-p DB_PORT] [-u DB_USER] [-P [DB_PASSWORD]] [-s DB_SCHEMA] [-U URL]
                           [-c CERT] [-k KEY] [-d USER_DN]

options:
  -h, --help            show this help message and exit
  -H DB_HOST, --db-host DB_HOST
                        The database hostname or IP address.
  -p DB_PORT, --db-port DB_PORT
                        The database port.
  -u DB_USER, --db-user DB_USER
                        The database user.
  -P [DB_PASSWORD], --db_password [DB_PASSWORD]
  -s DB_SCHEMA, --db-schema DB_SCHEMA
                        The database schema.
  -U URL, --url URL     The URL to OMSB. Defaults to the value of the OMSB_URL environment variable.
  -c CERT, --cert CERT  The path to the user's certificate. Defaults to value of the USER_CERT env variable.
  -k KEY, --key KEY     The path to the user's private key. Defaults to value of the USER_KEY env variable.
  -d USER_DN, --user-dn USER_DN
                        The user's distinguished name. Defaults to value of the USER_DN env variable.
```

Examples
--------
Run and listen for events from SQS::

    $ python -m oms_sensemaking geo


Natural Language Processing CLI
===============================

| **WARNING**: Not fully implemented

```
$python -m oms_sensemaking nlp -h
usage: oms_sensemaking nlp [-h]

options:
  -h, --help  show this help message and exit
```

Semantic CLI
============

| **WARNING**: Not fully implemented

```
$python -m oms_sensemaking semantic -h
usage: oms_sensemaking semantic [-h]

options:
  -h, --help  show this help message and exit
```
"""

import logging
import os
import time
from argparse import Action, ArgumentParser, Namespace
from getpass import getpass
from logging.config import dictConfig
from typing import Any, Optional, Sequence, Union

from dotenv import load_dotenv

from oms_sensemaking.nlp.corenlp_client import CoreNlpClient
from oms_sensemaking.nlp.nlp_reader import NlpFileReader

load_dotenv()

from oms_sdk import DEFAULT_ACM

from oms_sensemaking.config import SETTINGS, LogConfig
from oms_sensemaking.core.controllers import start_controller_and_wait

LOGGER = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging


class PasswordAction(Action):
    """An argparse action for handling passwords."""

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        """Use getpass to for safe (i.e. note echoed to console) password retrieval."""
        setattr(namespace, self.dest, getpass())


def add_db_cli_args(arg_parser: ArgumentParser) -> ArgumentParser:
    """
    Define common database CLI arguments on the given parser.

    :param arg_parser: The parser to initialize with common database arguments.
    :return: The configured arg_parser.
    """
    arg_parser.add_argument(
        "-H", "--db-host", default=os.getenv("DB_HOST", "127.0.0.1"), help="The database hostname or IP address."
    )
    arg_parser.add_argument("-p", "--db-port", default=SETTINGS.db_port or "5432", help="The database port.")
    arg_parser.add_argument("-u", "--db-user", default=SETTINGS.db_user or "appuser", help="The database user.")
    arg_parser.add_argument("-P", "--db_password", action=PasswordAction, nargs="?", default=SETTINGS.db_password)
    arg_parser.add_argument(
        "-s", "--db-schema", default=SETTINGS.db_schema or "oms_sensemaking", help="The database schema."
    )

    return arg_parser


def add_omsb_cli_args(parser: ArgumentParser) -> ArgumentParser:
    """
    Add the standard OMSB CLI options to the given parser.

    :param parser: A CLI parser.
    :return: the configured parser.
    """
    parser.add_argument(
        "-U",
        "--url",
        default="https://localhost:8020/graphql",
        help="The URL to OMSB. Defaults to https://localhost:8020/graphql.",
    )
    parser.add_argument(
        "-c",
        "--cert",
        default="./etc/pki/test10.pem",
        help="The path to the user's certificate. Defaults to ./etc/pki/test10.pem",
    )
    parser.add_argument(
        "-k",
        "--key",
        default="./etc/pki/test10.key",
        help="The path to the user's private key. Defaults to ./etc/pki/test10.key",
    )
    parser.add_argument(
        "-d",
        "--user-dn",
        default=os.getenv("USER_DN", "cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us"),
        help="The user's distinguished name. Defaults to value of the USER_DN env variable, if set, "
        "otherwise cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us",
    )
    parser.add_argument(
        "-a",
        "--aac-url",
        default="http://localhost:5022",
        help="The url for the AAC service. Defaults to http://localhost:5022",
    )
    # parser.add_argument("--pkcs12", default=os.getenv("PKCS12_FILE"),
    #                     help="The path to the user's PKCS12 file. Mutually exclusive from the --cert/--key options.")
    # parser.add_argument("--pkcs12-password", action=PasswordAction, nargs='?', default=os.getenv("PKCS12_PASSWORD"),
    #                     help="The PKCS12 password. If no value is provided, you will be prompted.")

    return parser


def run_geospatial(args: Namespace) -> None:
    """
    Run the geospatial algorithms.

    :param args: The command line arguments.
    """
    # override database settings
    SETTINGS.db_host = args.db_host
    SETTINGS.db_port = args.db_port
    SETTINGS.db_user = args.db_user
    SETTINGS.db_password = args.db_password
    SETTINGS.db_schema = args.db_schema

    # override osm_sdk settings
    SETTINGS.omsb_url = args.url
    SETTINGS.user_dn = args.user_dn
    SETTINGS.cert_path = args.cert
    SETTINGS.key_path = args.key
    SETTINGS.aac_url = args.aac_url
    # TODO: Handle PKCS12

    # lazy load controller to allow CLI args to override app config
    from oms_sensemaking.geospatial.controllers import GeospatialSensemakerController, GeoSQSListener

    geo: GeospatialSensemakerController = GeospatialSensemakerController(GeoSQSListener())

    start_controller_and_wait(geo)


def run_nlp(args: Namespace) -> None:
    """Run the NLP algorithms."""
    # lazy load controller to allow CLI args to override app config
    from oms_sensemaking.nlp.nlp_service import NlpService

    nlp_service = NlpService()
    nlp_reader = NlpFileReader(args.filename)
    nlp_service.run_service(
        acm=DEFAULT_ACM,
        nlp_reader=nlp_reader,
        source_id=args.source_id,
        corenlp_client=CoreNlpClient(props={}, hostname=SETTINGS.corenlp_localhost),
    )


def run_semantic() -> None:
    """Run the semantic algorithms."""
    # lazy load controller to allow CLI args to override app config
    from oms_sensemaking.core.events import DummyObjectEventConsumer
    from oms_sensemaking.semantic.controllers import SemanticSensemakerController

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
    geo_parser: ArgumentParser = add_omsb_cli_args(
        add_db_cli_args(subparsers.add_parser("geo", help="Run geospatial analytics."))
    )
    geo_parser.set_defaults(func=run_geospatial)

    # natural language processing subcommand
    nlp_parser: ArgumentParser = subparsers.add_parser("nlp", help="Run NLP analytics.")
    nlp_parser.add_argument("-f", "--filename", type=str, help="File to run on.")
    nlp_parser.add_argument("-id", "--source-id", type=str, help="Source ID of the text.")
    nlp_parser.set_defaults(func=run_nlp)

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

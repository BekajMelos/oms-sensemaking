import logging
import os

from dotenv import load_dotenv

load_dotenv()

DEBUG = os.environ.get("DEBUG", "false").lower() in ["true", "yes"]
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO


logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s-%(filename)s-%(levelname)s-%(message)s")
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(LOG_LEVEL)

from logging.config import dictConfig

from dotenv import load_dotenv
from oms_sensemaking.config import LogConfig

load_dotenv()
dictConfig(LogConfig().model_dump())  # initialize logging

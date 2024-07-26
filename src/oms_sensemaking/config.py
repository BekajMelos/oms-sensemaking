"""Application configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogConfig(BaseSettings):
    """Logging configuration to be set for the server."""

    logger_name: str = 'oms_sensemaker'

    log_format: str = '{asctime:<20s}{levelname:<8s}{name} {message}'
    log_level: str = 'DEBUG'

    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict[str, dict] = {
        'simple': {
            'format': "[%(asctime)s %(levelname)-7s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'standard': {
            'format': "[%(asctime)s - %(name)s - %(levelname)s - %(funcName)20s() ] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        }

    }
    handlers: dict[str, dict] = {
        'default': {
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr'
        }
    }
    loggers: dict[str, dict] = {
        '': {  # root logger
            'handlers': ['default'],
            'level': log_level,
            'propagate': False
        },
        logger_name: {
            'handlers': ['default'],
            'level': log_level
        },
        'omsb_common_util_python': {
            'level': 'DEBUG'
        }
    }


class Settings(BaseSettings):
    """Settings class."""

    model_config = SettingsConfigDict()

    # Geospatial Sensemaking Settings
    valid_observed_threshold_seconds: int = Field(
        900, description="Threshold for amount of between Track Point Observations"
    )
    cache_entry_expire_sec: int = Field(5, description="How long to wait for new points before creating a new Track")
    geohash_low: int = Field(5, description="Low geohash")
    geohash_high: int = Field(7, description="High geohash")
    poll_period_seconds: int = Field(10, description="How often to poll for new incoming Attributes")

    # Loiter Settings
    detect_loiters: bool = Field(True, description="Toggle on/off Loiter Detection")
    loiter_min_time: int = Field(900, description="Minimum amount of time for a valid Loiter Event")

    # Cotravel Settings
    detect_cotravels: bool = Field(True, description="Toggle on/off Cotravel Detection")
    min_cotravel_duration_seconds: int = Field(
        1200, description="Minimum between Objects in a Track for a Cotravel Event"
    )
    min_lag_lead_duration_seconds: int = Field(
        1200, description="Minimum amount between Objects in a Track for a Lag/Lead Event"
    )
    max_lag_lead_duration_seconds: int = Field(
        2700, description="Maximum between Objects in a Track for a Lag/Lead Event"
    )

    # Similar Track Settings
    similar_tracks: bool = Field(False, description="Toggle on/off Similar Track Calculations")
    n_tracks: int = Field(5, description="Number of similar tracks to return")
    within_meters: float = Field(3000.0, description="Used to define the search space for potential similar tracks")


SETTINGS: Settings = Settings()

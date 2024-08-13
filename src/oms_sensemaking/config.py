"""Application configuration."""

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogConfig(BaseSettings):
    """Logging configuration to be set for the server."""

    logger_name: str = "oms_sensemaker"
    log_format: str = "{asctime:<20s}{levelname:<8s}{name} {message}"
    log_level: str = "DEBUG"

    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict[str, dict] = {
        "simple": {
            "format": "[%(asctime)s %(levelname)-7s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "standard": {
            "format": "[%(asctime)s - %(name)s - %(levelname)s - %(funcName)20s() ] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict[str, dict] = {
        "default": {
            "formatter": "simple",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr"
        }
    }

    @computed_field
    @property
    def loggers(self) -> dict[str, dict]:
        """Compute loggers field based on other parameters (e.g. logger_name and log_level)."""
        return {
            "": {  # root logger
                "handlers": ["default"],
                "level": self.log_level,
                "propagate": False,
            },
            self.logger_name: {
                "handlers": ["default"],
                "level": self.log_level,
                "propagate": True
            },
            "oms_sdk": {
                "level": "DEBUG"
            },
            "boto3": {
                "level": "INFO"
            },
            "botocore": {
                "level": "INFO"
            },
            "urllib3": {
                "level": "INFO"
            },
            "httpcore": {
                "level": "INFO"
            }
        }


class Settings(BaseSettings):
    """Settings class."""
    model_config = SettingsConfigDict()

    gzip_minimum_size: int = 1000

    # Geospatial Sensemaking Settings
    valid_observed_threshold_seconds: int = Field(
        900, description="Threshold for amount of between Track Point Observations"
    )
    cache_entry_expire_sec: int = Field(30, description="How long to wait for new points before creating a new Track")
    geohash_low: int = Field(5, description="Low geohash")
    geohash_high: int = Field(7, description="High geohash")
    poll_period_seconds: int = Field(10, description="How often to poll for new incoming Attributes")
    operated_by_iri: str = Field(
        "http://schema.dia.mil/DefenseIntelligenceCoreOntology/operatedBy", description="IRI for Operated By"
    )

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

    # AWS SQS Settings
    sqs_queue_url: str = Field(
        "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/resolutionTrigger",
        description="SQS Queue URL",
    )
    aws_endpoint_url: str = Field("http://localhost:4566", description="SQS Endpoint")
    aws_access_key_id: str = Field("FAKE", description="AWS Access Key")
    aws_secret_access_key: str = Field("FAKE", description="AWS Secret Key")
    aws_region_name: str = Field("us-east-1", description="AWS Region")
    aws_use_ssl: bool = Field(False, description="Boolean to use SSL for SQS Connection")
    aws_verify: bool = Field(False, description="Boolean to use SSL verifiation for SQS Connection")
    sqs_read_loops: int = Field(
        20,
        description="Number of times to look for SQS messages. This number * 10 is how many "
        "messages can be received per poll",
    )
    sqs_read_wait_seconds: int = Field(5, description="How long to wait when waiting for SQS messages")
    omsb_url: str = Field("https://localhost:8443/graphql", description="URL for OMSB")
    user_dn: str = Field("cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us", description="User DN")
    cert_path: str = Field("./pki/test10.pem", description="Path to User PEM")
    key_path: str = Field("./pki/test10.key", description="Path to User Key")


SETTINGS: Settings = Settings()

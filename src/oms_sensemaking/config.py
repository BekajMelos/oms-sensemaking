"""Application configuration."""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, PostgresDsn, ValidationInfo, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_PATH: Path = Path(__file__).parent.parent.parent


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

    @computed_field  # type: ignore
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

    # database settings
    db_host: str = Field("localhost", description="Database hostname or IP address.")
    db_port: str = Field("5432", description="Database port.")
    db_user: str = Field("appuser", description="Database user.")
    db_password: str = Field("password", description="Database user's password.")
    db_schema: str = Field("oms_sensemaking", description="Database schema name.")
    db_uri: Optional[str] = Field(
        None, description="Database connection URI. This is an alternative to configuring the independent components."
    )

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

    @field_validator("db_uri", mode="before")
    @classmethod
    def db_connection(cls, field_value: Optional[str], info: ValidationInfo) -> str:
        """Validate database connection."""  # pylint: disable=too-many-function-args, no-self-argument
        return cls.assemble_db_connection(field_value, info.data, "db_")

    @classmethod
    def assemble_db_connection(
        cls, field_value: Optional[str], values: Dict[str, Any], settings_prefix: str = ""
    ) -> str:
        """
        Validate db connection.

        This function builds a PostgreSQL database connection string from a
        collection of related configuration properties if the target value is
        not set explicitly.
        """
        if isinstance(field_value, str):
            return field_value

        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=values.get(f"{settings_prefix}user"),
            password=values.get(f"{settings_prefix}password") or "",
            host=values.get(f"{settings_prefix}host") or "localhost",
            port=int(values.get(f"{settings_prefix}port") or 5432),
            path=values.get(f"{settings_prefix}schema") or ""
        ).unicode_string()


SETTINGS: Settings = Settings()

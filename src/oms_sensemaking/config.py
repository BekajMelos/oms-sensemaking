"""Application configuration."""
import json
import logging
import os
import re
from datetime import timedelta
from functools import cached_property
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from dotenv import load_dotenv
from oms_sdk.generated.generated_graphql_client import Confidence
from pydantic import BaseModel, Field, PostgresDsn, ValidationInfo, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_PATH: Path = Path(__file__).parent.parent.parent

LOGGER = logging.getLogger(__name__)

load_dotenv()


class LogConfig(BaseSettings):
    """Logging configuration to be set for the server."""

    version: int = 1
    disable_existing_loggers: bool = False
    logger_name: str = "oms_sensemaker"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"
    log_format: str = "{asctime:<20s}{levelname:<8s}{threadName:<32s} {name}: {message}"
    log_format_class: str = "logging.Formatter"
    log_format_style: str = "{"  # https://docs.python.org/3/howto/logging.html#formatters
    log_level: str = Field("INFO", alias='app_log_level')

    handlers: dict[str, dict] = {
        "default": {
            "formatter": "custom",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr"
        }
    }

    @computed_field  # type: ignore
    @property
    def formatters(self) -> dict[str, dict]:
        """
        Computed formatters field based on other parameters.

        The default configuration use the "{" style for logging formats.

        Examples:
            simple:   [{asctime}] {levelname:7s} {message}
            standard: [{asctime} - {name} - {levelname} - {funcName:20s} ] {message}
            default:  {asctime:<20s}{levelname:<8s}{name} {message}
        """
        return {
            "custom": {
                "()": self.log_format_class,
                "format": self.log_format,
                "datefmt": self.log_date_format,
                "style": self.log_format_style
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
            "uvicorn": {
                "handlers": ["default"],
                "level": self.log_level,
                "propagate": False
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": self.log_level,
                "propagate": False
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": self.log_level,
                "propagate": False
            },
            "oms_sdk": {
                "level": self.log_level
            },
            "httpcore": {
                "level": "INFO"
            },
            "httpx": {
                "level": "WARNING" if self.log_level == "INFO" else "INFO"
            },
            "urllib3": {
                "level": "INFO"
            },
            "pika": {
                "level": "INFO"
            }
        }


class MilSymbolSettings(BaseModel):
    symbol_attribute_iri: str = Field(
        "http://www.ontologyrepository.com/CommonCoreOntologies/has_text_value",
        description="Military Symbol Sensemaker tags")
    mil_symbol_sensemaker_tags: list[str] = Field(
        ["Oms Sensemaking", "Military Symbol Sensemaker"],
        description="Military Symbol Sensemaker tags"
    )
    rmq_mil_symbol_queue_name: str = Field(
        "mil-symbol-trigger",
        description="the RMQ Resolution Queue name",
        examples=["mil-symbol-trigger"]
    )
    enable_mil_symbol_sensemaker: bool = Field(True, description="Toggle on/off Mil Symbol Sensemaking")
    affiliation_iris: list[str] = Field(
        ["https://oms.dodiis.ic.gov/ontology/p-0000000033"], description="Affiliation IRI")
    status_iris: list[str] = Field(["https://foundry.ai.mil/ontology/4901-001/hasCondition"], description="Status IRI")
    echelon_iris: list[str] = Field(["https://oms.dodiis.ic.gov/ontology/p-0000000029"], description="Echelon IRI")
    affiliation_controlled_by_iris: list[str] = Field(
        ["https://foundry.ai.mil/ontology/4901-001/controlledBy"],
        description="Relationship IRIs used to search for controlling/commanding nodes")
    affiliation_controls_iris: list[str] = Field(
        ["https://foundry.ai.mil/ontology/4901-001/controls"],
        description="Relationship IRIs used to search for controlling/commanding nodes"
    )
    attribute_code_iris: list[str] = Field(
        ["http://www.ontologyrepository.com/CommonCoreOntologies/has_text_value"],
        description="Attribute Iris for full mil symbol codes")

    # 2525B and 2525C placeholders
    b_c_placeholders: list[str] = Field(
        ["-", "*"],
        description="Possible placeholder values for 2525B and 2525C codes"
        )

    # War, Pending, Unknown, Present
    default_2525b_code: str = Field(
        "SUZP------*****", description="Default 2525B code")
    default_2525c_code: str = Field(
        "SUZP------*****", description="Default 2525C code")
    # Reality, Pending, Unknown, Present, Military
    default_2525d_code: str = Field(
       "10-0-0-00-0-0-00-000000-00-00", description="Default 2525C code")

    # TODO should we skip a default since these are random
    is_reality_context_iris: list[str] = Field(
        ["https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted"],
        description="Attribute Iri to look for 'is reality' context")
    is_exercise_context_iris: list[str] = Field(
        ["https://foundry.ai.mil/MIDB_GST/v1/Target_Validated"],
        description="Attribute Iri to look for 'is exercise' context")
    is_simulation_context_iris: list[str] = Field(
        ["https://foundry.ai.mil/MIDB_GST/v1/Target_Restriction"],
        description="Attribute Iri to look for 'is simulation' context")

    rules_file_path: str = Field("./data/mil_symbol_rules.json", description="Path to the rules config file")

# IW Settings
class IWSettings(BaseModel):
    """Settings for I&W"""

    max_observables_to_process: int = Field(500, description="Max page size to limit observations query")

    observable_query_interval: timedelta = Field(
        timedelta(minutes=15),
        description="Minutes between each observable query"
    )

    observable_statuses: dict = Field({
        "unknown": "Unknown",
        "not_observed": "Not Observed",
        "partially_observed": "Partially Observed",
        "fully_observed": "Observed"
    }, description="Status options for the observable")

    observable_config_attribute_iri: str = Field(
        "http://www.ontologyrepository.com/CommonCoreOntologies/has_text_value",
        description="Config attribute used to read the settings of an observable query")

    observable_status_attribute_iri: str = Field(
        "https://foundry.ai.mil/ontology/4901-001/hasOperationalStatus",
        description="Status attribute used to indicate the status of an observable")

    observable_location_attribute_iri: str = Field(
        "https://oms.dodiis.ic.gov/ontology/p-0000000140",
        description="Location attribute used to identify the boundary of an observable")

    observable_associated_with_relationship_iri: str = Field(
        "https://oms.dodiis.ic.gov/ontology/p-0000000034",
        description="Relationship used to associate an observable with an object")

class Settings(BaseSettings):
    """Settings class."""

    model_config = SettingsConfigDict(env_nested_delimiter="__")

    gzip_minimum_size: int = 1000

    oms_version_env: str = Field(os.getenv("OMSB_VERSION") or "", description="Current version of OMS")

    # OMS_SDK-related settings
    create_source_if_none: bool = Field(False, description="Allow creation of source")
    create_provider_if_none: bool = Field(False, description="Allow creation of provider")

    # General IRIs
    track_iri: str = Field("https://foundry.ai.mil/ontology/4901-001/ObjectTrack", description="IRI for Tracks")

    # Request Rate Settings
    maximum_oms_api_calls: int = Field(5000,
                                       description="Maximum amount of requests made to the OMS API per time period")
    oms_api_call_period_seconds: int = Field(30,
                                             description="Alloted amount of time for maximum OMS API calls to be made")

    # Labels
    sm_connected_track: str = Field("SM_CONNECTED_TRACK", description="Label for tracks generated by sensemaking")
    sm_enriched_label: str = Field("SM_ENRICHED", description="Label for enriched sensemaking data")
    sm_inferenced_label: str = Field("SM_INFERENCED", description="Label for all sensemaking generated data")
    geospatial_sm_label: str = Field("GEOSPATIAL_SM", description="Label for geospatial sensemaking data")
    cotravel_sm_label: str = Field("COTRAVEL_SM", description="Label for cotravel sensemaker")
    loiter_sm_label: str = Field("LOITER_SM", description="Label for loiter sensemaker data")
    inference_sm_label: str = Field("INFERENCE_SM", description="Label for inference sensemaking data")
    incursion_sm_label: str = Field("INCURSION_RULE", description="Label for incursion sensemaking data")
    garrison_sm_label: str = Field("IN/OUT_GARRISON_RULE", description="Label for garrison sensemaking data")
    mil_sym_sm_label: str = Field("MILITARY_SYMBOL_SM", description="Label for mil sym sensemaking data")
    res_sm_label: str = Field("RESOLUTION_SM", description="Label for resolution sensemaking data")

    # Classification Banner Settings
    classification_banner_text: str = Field("UNCLASSIFIED", description="Text to display in the classification banner")
    classification_banner_color: str = Field("#00c853", description="Background color for the classification banner")

    # Inference Settings
    generate_inferences: bool = Field(True, description="Turn the Inference Sensemaker on and off")
    toggle_add_garrison_rule: bool = Field(True, description="Toggle on/off Add Garrison Attr. Rule")
    toggle_incursion_rule: bool = Field(True, description="Toggle on/off Incursion Rule")
    inference_tags: list[str] = Field(
        ["Oms Sensemaking", "Inferred Data"], description="Inference Sensemaker tags"
    )
    incursion_tags: list[str] = Field(
        ["Oms Sensemaking", "Inferred Data", "Incursion"], description="Incursion tags"
    )
    inference_incursion_activity_state: str = Field(
        "UNKNOWN", description="String Incursion Activity State"
    )
    inference_incursion_areas_of_interest_path: str = Field(
        "./data/areas_of_interest", description="Path to areas of interest file"
    )
    inference_incursion_class_iri: str = Field(
        "http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct", description="IRI for incursion class"
    )
    inference_incursion_attribute_iri: str = Field(
        "https://foundry.ai.mil/ontology/4901-001/hasCoordinates",
        description="IRI for incursion attribute"
    )
    inference_geo_attribute_iri: str = Field(
        "https://foundry.ai.mil/ontology/4901-001/hasCoordinates", description="IRI for geo attribute"
    )
    inference_garrisoned_in_iri: str = Field(
        "https://foundry.ai.mil/ontology/4901-001/garrisonedIn",
        description="IRI for relationship between an object and its garrison"
    )
    inference_garrison_class_iri: str = Field(
        "http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct",
        description="IRI for garrison activity class"
    )
    inference_in_garrison_activity_name: str = Field(
        "In Garrison", description="Name for In Garrison activities"
    )
    inference_out_of_garrison_activity_name: str = Field(
        "Out of Garrison", description="Name for Out of Garrison activities"
    )
    inference_in_garrison_activity_state: str = Field(
        "IN_GARRISON", description="String In Garrison Activity State"
    )
    inference_out_of_garrison_activity_state: str = Field(
        "OUT_OF_GARRISON", description="String Out of Garrison Activity State"
    )
    garrison_distance_kilometers: int = 2000

    # database settings
    db_host: str = Field("localhost", description="Database hostname or IP address.")
    db_port: str = Field("5432", description="Database port.")
    db_user: str = Field(description="Database user.")
    db_password: str = Field(description="Database user's password.")
    db_schema: str = Field("oms_sensemaking", description="Database schema name.")
    db_uri: str | None = Field(
        None, description="Database connection URI. This is an alternative to configuring the independent components."
    )
    db_ssl: bool = Field(True, description="Flag to require SSL verse just preferring SSL.")

    # Geospatial Sensemaking Settings
    geo_sensemaker_config_file_path: str = Field("data/geo_sensemaker_config.json",
                                                 description="Path to the Geospatial Sensemaker Config")
    srid: int = Field(4326, description="Spatial Reference Identifier for storing/handling Points")
    cache_entry_expire_sec: int = Field(30, description="How long to wait for new points before creating a new Track")
    poll_period_seconds: int = Field(10, description="How often to poll for new incoming Attributes")
    geo_sensemaker_event_tag: str = Field("geosensemaker_tag",
        description="Tag for OMSB objects from the geospatial sensemakers")
    max_track_time_length_seconds: int = Field(7 * 24 * 60 * 60,
        description="Max amount of time in seconds a track can be from earliest start time to last start time",
        examples=[86400, 604800])
    geo_sensemaker_config_default_provider_id: str = Field(
        "00000000-0000-0000-0000-000000000000",
        description="Default provider ID in geo sensemaker config file"
    )

    # Common Sense Filtering Settings
    apply_common_sense_filters: bool = Field(True, description="Toggle on/off Common Sense Filters")
    common_sense_filter_rules_file_path: str = Field(
        "./data/common_sense_filter_rules.json",
        description="Path to the rules config file",
    )

    # Track Weaver Settings
    track_weaver_algorithm: str = Field(
        "naive",
        description="The algorithm to use for making tracks",
        examples=["naive", "time_bin_weighted_average"]
    )
    time_bin_size_seconds: int = Field(
        60,
        description="Length of time bins in seconds for grouping Points in track weaver."
    )
    confidence_weight_unknown: float = Field(0.5, description="Weight assigned to UNKNOWN confidence.")
    confidence_weight_high: float = Field(1.0, description="Weight assigned to HIGH confidence.")
    confidence_weight_moderate: float = Field(0.5, description="Weight assigned to MODERATE confidence.")
    confidence_weight_low: float = Field(0.25, description="Weight assigned to LOW confidence.")

    # Loiter Settings
    detect_loiters: bool = Field(True, description="Toggle on/off Loiter Detection")
    loiter_event_name: str = Field("LoiterEvent", description="Name prefix for OMSB Loiter Event Nodes")
    loiter_event_node_iri: str = Field("http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct",
                                   description="OMSB Loiter Event Node IRI")
    loiter_relationship_iri: str = Field("http://purl.obolibrary.org/obo/BFO_0000197",
                                         description="OMSB Loiter Event Node to Track Relationship IRI")
    loiter_event_node_attribute_iri: str = Field("https://foundry.ai.mil/ontology/4901-001/hasCoordinates",
                                                 description="OMSB Loiter Event Node Geo Attribute IRI")

    # Cotravel Settings
    detect_cotravels: bool = Field(True, description="Toggle on/off Cotravel Detection")

    potential_duplicate_relationship_name: str = Field("Potential Duplicate",
                                                       description="Name for OMSB Potential Duplicate")
    cotravel_event_name: str = Field("Cotravel", description="Name prefix for OMSB Cotravel Event Nodes")
    lag_lead_event_name: str = Field("LagLead", description="Name prefix for OMSB LagLead Event Nodes")
    cotravel_event_node_iri: str = Field("http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct",
                                   description="OMSB Cotravel Event Node IRI")
    cotravel_relationship_iri: str = Field("http://purl.obolibrary.org/obo/BFO_0000197",
                                         description="OMSB Cotravel Event Node to Track Relationship IRI")
    cotravel_event_node_attribute_iri: str = Field("https://foundry.ai.mil/ontology/4901-001/hasCoordinates",
                                                 description="OMSB Cotravel Event Node Geo Attribute IRI")
    cotravel_track_to_event_relation_name: str = Field("inheres in",
                                                 description="OMSB Cotravel Event Node to Track Relationship Name")

    # Similar Track Settings
    similar_tracks: bool = Field(True, description="Toggle on/off Similar Track Calculations")
    n_tracks: int = Field(5, description="Number of similar tracks to return")

    # RabbitMQ Settings
    rabbitmq_host: str = Field("rabbitmq", description="RabbitMQ host")
    rabbitmq_port: int = Field(5672, description="RabbitMQ port")
    rabbitmq_vhost: str = Field("/", description="RabbitMQ virtual host")
    rabbitmq_username: str = Field(description="RabbitMQ username")
    rabbitmq_password: str = Field(description="RabbitMQ password")
    rabbitmq_prefetch_count: int = Field(200, description="RabbitMQ prefetch count")

    rmq_read_wait_seconds: int = Field(5, description="How long to wait when waiting for RMQ messages")
    rmq_geo_queue_name: str = Field(
        "geo-sensemaker-trigger",
        description="the RMQ Geo Sensemaker Queue name",
        examples=["geo-sensemaker-trigger"]
    )
    rmq_inference_queue_name: str = Field(
        "infer-sensemaker-trigger",
        description="the RMQ Inference Sensemaker Queue name",
        examples=["infer-sensemaker-trigger"]
    )

    # Resolution Sensemaker Settings
    rmq_res_queue_name: str = Field(
        "resolution-trigger",
        description="the RMQ Resolution Queue name",
        examples=["resolution-trigger"]
    )
    enable_resolution_sensemaker: bool = Field(True, description="Toggle on/off Entity Resolution")
    resolution_sensemaker_tag: str = Field("resolution_tag",
                                           description="Tag for OMSB objects from the resolution sensemaker")
    resolution_relationship_name: str = Field("Same As",
                                           description="Relationship IRI for resolution sensemaker suggestions")
    resolution_relationship_iri: str = Field("http://www.ontologyrepository.com/CommonCoreOntologies/is_about",
                                           description="Relationship IRI for resolution sensemaker suggestions")
    # Placeholder IRI
    duplicate_object_iris_file_path: str = Field(
        "./data/duplicate_object_iris.json", description="Path to file containing duplicate object iris dictionary"
    )

    mil_symbol_settings: MilSymbolSettings = MilSymbolSettings()

    iw_settings: IWSettings = IWSettings()
    observables: bool = Field(True, description="Toggle on/off Observable updates")

    # Connectivity ping settings
    ping_timeout_seconds: float = Field(3.0, description="Default timeout in seconds for service ping checks")
    ping_wait_retries: int = Field(5, description="Default number of retries when waiting for service readiness")
    ping_wait_delay_seconds: float = Field(2.0, description="Delay between readiness retries in seconds")

    omsb_url: str = Field("https://omsb2:8443/graphql", description="URL for OMSB")
    omsb_host: str = Field("omsb2", description="OMSB hostname or IP address")
    omsb_port: int = Field(8443, description="OMSB port")
    omsb_version: str = Field("Grimlock-INC-30", description="OMSB Version")
    aac_url: str = Field("http://aac2:3000", description="URL for AAC")
    aac_host: str = Field("aac2", description="AAC hostname or IP address")
    aac_port: int = Field(3000, description="AAC port")
    user_dn: str = Field(description="User DN")
    cacert_path: str | None = Field(
        None,
        description="Optional path to a CA cert",
        examples=[None, "/opt/common/pki/cacert.pem"])
    cert_path: str | None = Field(
        None,
        description="Path to service user cert",
        examples=[None, "/opt/common/pki/sensemaking.pem"]
    )
    key_path: str | None = Field(
        None,
        description="Path to service user key",
        examples=[None, "/opt/common/pki/sensemaking.key"]
    )
    pkcs12_path: str | None = Field(
        None,
        description="Optional path to a pkcs12 cert",
        examples=[None, "/opt/common/pki/my_cert.pfx", "/opt/common/pki/my_cert.p12"])
    pkcs12_password: str | None = Field(
        None,
        description="Optional password to a pkcs12 cert",
        examples=[None, "p@55w0rd"])
    aac_verification_mode: bool = Field(
        True,
        description="""Optional param for verifying ssl connections to the AAC Service
        `True` will use the Default CA Bundle or an SSL Context if a CA_CERT_PATH is given
        `False` will disable verification""",
        examples=[True, False]
    )
    aac_cache_enabled: bool = Field(True, description="Whether to use cached responses from AAC")
    aac_cache_storage_ttl_seconds: int = Field(300, description="How long cached responses should be stored")

    root_path: str = Field("", description="BaseUrl to the service", examples=["/services/sensemaking/1.0", ""])

    enable_audit_log_error_logging: bool = Field(True, description="Enable logging of sensemaking errors")
    audit_log_error_max_tb_chars: int = Field(200, ge=0, description="Max length for audit log error tracebacks")
    audit_log_error_json_file_path: str = Field(
        "./data/audit_log_error_acm.json",
        description="Path to the audit event log error classification file")

    rethrow_errors_enabled: bool = Field(True, description="Enable rethrowing of sensemaking errors")

    user_dn_whitelist_path: str = Field("./data/whitelist.txt", description="Path to User Whitelist")

    @computed_field  # type: ignore
    @cached_property
    def user_dn_whitelist(self) -> list[str]:
        """Return classification as json from audit_log_error_json_file_path"""
        with open(SETTINGS.user_dn_whitelist_path, "r") as fd:
            return fd.read().lower().splitlines()

    @computed_field  # type: ignore
    @cached_property
    def audit_log_error_acm(self) -> dict[str, str]:
        """Return classification as json from audit_log_error_json_file_path"""
        with open(self.audit_log_error_json_file_path, encoding="utf-8") as fd:
            return json.load(fd)

    def load_audit_log_event_error_acm(self):
        """Load audit event log error classification from file
        This should be done on startup to ensure file exists
        """
        if SETTINGS.audit_log_error_acm:
            LOGGER.info("Loaded audit log error classification")

    @computed_field  # type: ignore
    @property
    def confidence_weight_map(self) -> dict[Confidence, float]:
        return {
            Confidence.UNKNOWN: self.confidence_weight_unknown,
            Confidence.HIGH: self.confidence_weight_high,
            Confidence.MODERATE: self.confidence_weight_moderate,
            Confidence.LOW: self.confidence_weight_low,
        }

    @field_validator("db_uri", mode="before")
    @classmethod
    def db_connection(cls, field_value: str | None, info: ValidationInfo) -> str:
        """Validate database connection."""  # pylint: disable=too-many-function-args, no-self-argument
        return cls.assemble_db_connection(field_value, info.data, "db_")

    @classmethod
    def assemble_db_connection(
        cls, field_value: str | None, values: dict[str, Any], settings_prefix: str = ""
    ) -> str:
        """
        Validate db connection.

        This function builds a PostgreSQL database connection string from a
        collection of related configuration properties if the target value is
        not set explicitly.
        """
        if isinstance(field_value, str):
            return field_value
        encoded_pw = quote_plus(values.get(f"{settings_prefix}password") or "")

        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=values.get(f"{settings_prefix}user"),
            password=encoded_pw,
            host=values.get(f"{settings_prefix}host") or "localhost",
            port=int(values.get(f"{settings_prefix}port") or 5432),
            path=values.get(f"{settings_prefix}schema") or ""
        ).unicode_string()

    @field_validator("classification_banner_text", mode="before")
    @classmethod
    def validate_classification_banner_text(cls, field_value: str, info: ValidationInfo) -> str:
        """Validate that the classification banner text does not contain HTML."""
        if re.search(r"<[^>]*>", field_value):
            raise ValueError("Classification banner text cannot contain HTML.")
        return field_value

    @field_validator("classification_banner_color", mode="before")
    @classmethod
    def validate_classification_banner_color(cls, field_value: str, info: ValidationInfo) -> str:
        """Validate that the classification banner color is a valid hex color."""
        if not re.match(r"^#([A-Fa-f0-9]{3}){1,2}$", field_value):
            raise ValueError("Classification banner color must be a valid hex color (e.g., #00c853).")
        return field_value


SETTINGS: Settings = Settings()

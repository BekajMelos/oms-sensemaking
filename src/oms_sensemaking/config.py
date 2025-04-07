"""Application configuration."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, PostgresDsn, ValidationInfo, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_PATH: Path = Path(__file__).parent.parent.parent

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
    log_level: str = Field("WARNING", alias='app_log_level')

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
            "oms_sdk": {
                "level": self.log_level
            },
            "boto3": {
                "level": "INFO"
            },
            "botocore": {
                "level": "INFO"
            },
            "httpcore": {
                "level": "INFO"
            },
            "httpx": {
                "level": "WARNING" if self.log_level == "INFO" else "INFO"
            },
            "urllib3": {
                "level": "INFO"
            }
        }


class MilSymbolSettings(BaseModel):
    symbol_attribute_iri: str = Field(
        "https://foundry.ai.mil/INDOPACOM/v5/Icon", description="Military Symbol Sensemaker tags")
    mil_symbol_sensemaker_tags: List[str] = Field(
        ["Oms Sensemaking", "Military Symbol Sensemaker"],
        description="Military Symbol Sensemaker tags"
    )
    sqs_mil_symbol_queue_url: str = Field(
        "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/milSymbolTrigger",
        description="the SQS Resolution Queue URL",
        examples=["http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/milSymbolTrigger"]
    )
    enable_mil_symbol_sensemaker: bool = Field(True, description="Toggle on/off Mil Symbol Sensemaking")
    affiliation_iris: List[str] = Field(
        ["https://foundry.ai.mil/MIDB_GST/v1/Affiliation"], description="Affiliation IRI")
    status_iris: List[str] = Field(["https://foundry.ai.mil/DICO/v3.1.0/Condition"], description="Status IRI")
    affiliation_controlled_by_iris: List[str] = Field(
        ["http://schema.dia.mil/DefenseIntelligenceCoreOntology/controlledBy"],
        description="Relationship IRIs used to search for controlling/commanding nodes")
    affiliation_controls_iris: List[str] = Field(
        ["https://foundry.ai.mil/MIDB/V3.3/commands_or_controls"],
        description="Relationship IRIs used to search for controlling/commanding nodes"
    )

    # War, Pending, Unknown, Present
    default_2525c_code: str = Field(
        "SUZP------*****", description="Default 2525C code")
    # Reality, Pending, Unknown, Present, Military
    default_2525d_code: str = Field(
       "10-0-0-00-0-0-00-000000-00-00", description="Default 2525C code")

    # TODO should we skip a default since these are random
    is_reality_context_iris: List[str] = Field(
        ["https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted"],
        description="Attribute Iri to look for 'is reality' context")
    is_exercise_context_iris: List[str] = Field(
        ["https://foundry.ai.mil/MIDB_GST/v1/Target_Validated"],
        description="Attribute Iri to look for 'is exercise' context")
    is_simulation_context_iris: List[str] = Field(
        ["https://foundry.ai.mil/MIDB_GST/v1/Target_Restriction"],
        description="Attribute Iri to look for 'is simulation' context")

    rules_file_path: str = Field("./data/mil_symbol_rules.json", description="Path the the rules config file")


class Settings(BaseSettings):
    """Settings class."""

    model_config = SettingsConfigDict(env_nested_delimiter="__")

    gzip_minimum_size: int = 1000

    oms_version_env: str = Field(os.getenv("OMSB_VERSION") or "", description="Current version of OMS")

    # OMS_SDK-related settings
    create_source_if_none: bool = Field(False, description="Allow creation of source")
    create_provider_if_none: bool = Field(False, description="Allow creation of provider")

    # General IRIs
    url_iri: str = Field("https://foundry.ai.mil/MIDB_GST/v1/Web_Site_URL", description="URL IRI")
    identifier_iri: str = Field("https://foundry.ai.mil/INDOPACOM/v5/ID_Number", description="Identifier IRI")
    text_iri: str = Field("https://foundry.ai.mil/DICO/v3.1.0/non_specific_Object", description="Text IRI")

    # Inference Settings
    generate_inferences: bool = Field(True, description="Turn the Inference Sensemaker on and off")
    toggle_add_garrison_rule: bool = Field(False, description="Toggle on/off Add Garrison Attr. Rule")
    toggle_add_has_name_rule: bool = Field(True, description="Toggle on/off Add Has Name Attr. Rule")
    toggle_incursion_rule: bool = Field(True, description="Toggle on/off Incursion Rule")
    inference_tags: list[str] = Field(
        ["Oms Sensemaking", "Inferred Data"], description="Inference Sensemaker tags"
    )
    incursion_tags: list[str] = Field(
        ["Oms Sensemaking", "Inferred Data", "Incursion"], description="Incursion tags"
    )
    inference_incursion_areas_of_interest_path: str = Field(
        "./data/areas_of_interest.json", description="Path to areas of interest file"
    )
    inference_incursion_class_iri: str = Field(
        "http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct", description="IRI for incursion class"
    )
    inference_incursion_attribute_iri: str = Field(
        "https://blackcape.io/PLACEHOLDER/Incursion", description="IRI for incursion attribute (placeholder)"
    )
    inference_add_has_name_attribute_iri: str = Field(
        "https://foundry.ai.mil/INDOPACOM/v5/Name", description="IRI for Name attributes"
    )
    inference_add_has_name_attribute_meta_data_iri: str = Field(
        "https://foundry.ai.mil/MIDB_GST/v1/MDN", description="IRI for generated meta data"
    )
    inference_add_garrison_attribute_iri: str = Field(
        "https://blackcape.io/PLACEHOLDER/inGarrison", description="IRI for geo attribute (placeholder)"
    )
    inference_participated_in_iri: str = Field(
        "https://blackcape.io/PLACEHOLDER/participatedIn", description="IRI for participated in (Observational)"
    )
    inference_garrison_location_iri: str = Field(
        "https://blackcape.io/PLACEHOLDER/garrisonedLocation", description="IRI for garrisoned at (Primary/Derivative)"
    )
    inference_add_in_garrison_iri: str = Field(
        "https://blackcape.io/PLACEHOLDER/isgarrisonedAt", description="IRI for adding a is garrisoned at"
    )
    garrison_distance_kilometers: int = 2000

    # NLP Settings
    corenlp_localhost: str = Field("localhost:9000",
                              description="Host and port for CoreNLP when running local script.")
    corenlp_host: str = Field("host.docker.internal:9000",
                                   description="Host and port for CoreNLP.")
    nlp_configuration: dict = Field(
        {"NER Model": "Default CoreNLP NER", "Relationship Extraction Model": "Default CoreNLP Relation Extraction"},
        description="Configuration of the NLP NER/Relationship extraction algorithm"
    )
    algorithm_version: str = Field(os.getenv("NLP_SENSEMAKER_VERSION") or "", description="NLP Sensemaker version")
    nlp_algorithm_name: str = Field("NER/Relationship Extraction", description="NLP algorithm name")
    nlp_tags: list[str] = Field(["SENSEMAKING_NLP"], description="Tags describing origin of node")
    corenlp_client_props: dict = Field(
        {
            "annotators": "tokenize, pos, lemma, ner, depparse, relation",
            "outputFormat": "text",
            "ner.model": "ner-model.ser.gz",
            "relation.model": "relation-model.ser.gz"
        },
        description="Properties to instantiate the CoreNLP client with."
    )

    # NLP Node IRIs (change once custom model is trained)
    nlp_node_iris: dict = Field({
            "Person": "http://www.ontologyrepository.com/CommonCoreOntologies/Person",
            "Organization": "http://www.ontologyrepository.com/CommonCoreOntologies/Organization",
            "Location": "http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation",
            "Document": "https://foundry.ai.mil/NIEM/v5.2/DocumentType",
            "Date": "https://foundry.ai.mil/NIEM/v5.2/DateType",
            "Entity": "http://purl.obolibrary.org/obo/BFO_0000001",
        },
        description="Dictionary of NLP Node IRIs"
        )
    nlp_default_node_iri: str = Field("http://purl.obolibrary.org/obo/BFO_0000001", description="Default NLP Node IRI")

    # NLP Relationship IRIs
    nlp_relationship_iris: dict = Field({
            "Work_For": "https://foundry.ai.mil/MIDB/V3.3/is_commanded_or_controlled_organizationally_by",
            "Live_In": "http://purl.obolibrary.org/obo/BFO_0000171",
            "OrgBased_In": "http://purl.obolibrary.org/obo/BFO_0000170",
            "Located_In": "http://purl.obolibrary.org/obo/BFO_0000171",
            "Document_Contains_Entity": "http://www.ontologyrepository.com/CommonCoreOntologies/describes",
            "Relates_To": "https://foundry.ai.mil/MIDB/V3.3/relates_to",
        },
        description="Dictionary of NLP Relationship IRIs"
        )
    nlp_default_relationship_iri: str = Field("https://foundry.ai.mil/MIDB/V3.3/relates_to",
                                              description="Default NLP Relationship IRI")

    # database settings
    db_host: str = Field("localhost", description="Database hostname or IP address.")
    db_port: str = Field("5432", description="Database port.")
    db_user: str = Field("appuser", description="Database user.")
    db_password: str = Field("password", description="Database user's password.")
    db_schema: str = Field("oms_sensemaking", description="Database schema name.")
    db_uri: Optional[str] = Field(
        None, description="Database connection URI. This is an alternative to configuring the independent components."
    )
    db_ssl: bool = Field(True, description="Flag to require SSL verse just preferring SSL.")

    # Geospatial Sensemaking Settings
    srid: int = Field(4326, description="Spatial Reference Identifier for storing/handling Points")
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
    geo_sensemaker_event_tag: str = Field("geosensemaker_tag",
                                          description="Tag for OMSB objects from the geospatial sensemakers")

    # Loiter Settings
    detect_loiters: bool = Field(True, description="Toggle on/off Loiter Detection")
    loiter_min_time: int = Field(900, description="Minimum amount of time for a valid Loiter Event")
    loiter_event_name: str = Field("LoiterEvent", description="Name prefix for OMSB Loiter Event Nodes")
    loiter_event_node_iri: str = Field("http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct",
                                   description="OMSB Loiter Event Node IRI")
    loiter_relationship_iri: str = Field("http://purl.obolibrary.org/obo/BFO_0000197",
                                         description="OMSB Loiter Event Node to Track Relationship IRI")
    loiter_event_node_attribute_iri: str = Field("https://foundry.ai.mil/INDOPACOM/v5/Location",
                                                 description="OMSB Loiter Event Node Geo Attribute IRI")

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

    cotravel_event_name: str = Field("CotravelEvent", description="Name prefix for OMSB Cotravel Event Nodes")
    lag_lead_event_name: str = Field("LagLeadEvent", description="Name prefix for OMSB LagLead Event Nodes")
    cotravel_event_node_iri: str = Field("http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct",
                                   description="OMSB Cotravel Event Node IRI")
    cotravel_relationship_iri: str = Field("http://purl.obolibrary.org/obo/BFO_0000197",
                                         description="OMSB Cotravel Event Node to Track Relationship IRI")
    cotravel_event_node_attribute_iri: str = Field("https://foundry.ai.mil/INDOPACOM/v5/Location",
                                                 description="OMSB Cotravel Event Node Geo Attribute IRI")
    cotravel_track_to_event_relation_name: str = Field("inheres in",
                                                 description="OMSB Cotravel Event Node to Track Relationship Name")

    # Similar Track Settings
    similar_tracks: bool = Field(True, description="Toggle on/off Similar Track Calculations")
    n_tracks: int = Field(5, description="Number of similar tracks to return")
    within_meters: float = Field(3000.0, description="Used to define the search space for potential similar tracks")

    # AWS SQS Settings
    aws_endpoint_url: str = Field("http://localhost:4566", description="SQS Endpoint")
    aws_access_key_id: str = Field("FAKE", description="AWS Access Key")
    aws_secret_access_key: str = Field("FAKE", description="AWS Secret Key")
    aws_region_name: str = Field("us-east-1", description="AWS Region")
    aws_use_ssl: bool = Field(False, description="Boolean to use SSL for SQS Connection")
    aws_verify: bool = Field(False, description="Boolean to use SSL verification for SQS Connection")

    sqs_read_loops: int = Field(
        20,
        description="Number of times to look for SQS messages. This number * 10 is how many "
        "messages can be received per poll",
    )
    sqs_read_wait_seconds: int = Field(5, description="How long to wait when waiting for SQS messages")
    sqs_geo_queue_url: str = Field(
        "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/geoSensemakerTrigger",
        description="the SQS Geo Sensemaker Queue URL",
        examples=["http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/geoSensemakerTrigger"]
    )
    sqs_inference_queue_url: str = Field(
        "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/inferenceSensemakerTrigger",
        description="the SQS Inference Sensemaker Queue URL",
        examples=["http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/inferenceSensemakerTrigger"]
    )

    # Resolution Sensemaker Settings
    sqs_res_queue_url: str = Field(
        "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/resolutionTrigger",
        description="the SQS Resolution Queue URL",
        examples=["http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/resolutionTrigger"]
    )
    enable_resolution_sensemaker: bool = Field(True, description="Toggle on/off Entity Resolution")
    resolution_sensemaker_tag: str = Field("resolution_tag",
                                           description="Tag for OMSB objects from the resolution sensemaker")
    resolution_relationship_name: str = Field("Same As",
                                           description="Relationship IRI for resolution sensemaker suggestions")
    resolution_relationship_iri: str = Field("https://foundry.ai.mil/MIDB/V3.3/relates_to",
                                           description="Relationship IRI for resolution sensemaker suggestions")
    duplicate_object_iris_file_path: str = Field(
        "./data/duplicate_object_iris.json", description="Path to file containing duplicate object iris dictionary"
    )

    mil_symbol_settings: MilSymbolSettings = MilSymbolSettings()


    omsb_url: str = Field("https://omsb2:8443/graphql", description="URL for OMSB")
    omsb_version: str = Field("Grimlock-INC-17", description="OMSB Version")
    aac_url: str = Field("http://aac2:3000", description="URL for AAC")
    user_dn: str = Field("cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us", description="User DN")
    cert_path: str = Field(
        "/opt/common/pki/server.public",
        description="Path to service user cert",
        examples=["/opt/common/pki/sensemaking.pem"]
    )
    key_path: str = Field(
        "/opt/common/pki/server.private",
        description="Path to service user key",
        examples=["/opt/common/pki/sensemaking.key"]
    )
    root_path: str = Field("", description="BaseUrl to the service", examples=["/services/sensemaking/1.0", ""])

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

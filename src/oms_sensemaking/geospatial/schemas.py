
from pydantic import BaseModel, Field


class GeospatialSensemakerConfig(BaseModel):
    valid_observed_threshold_seconds: int = Field(
        900, description="Threshold for amount of between Track Point Observations"
    )
    geohash_low: int = Field(5, description="Low geohash")
    geohash_high: int = Field(7, description="High geohash")

    # Loiter Settings
    loiter_min_time: int = Field(900, description="Minimum amount of time for a valid Loiter Event")

    # Cotravel settings
    min_cotravel_duration_seconds: int = Field(
        1200, description="Minimum between Objects in a Track for a Cotravel Event"
    )
    min_lag_lead_duration_seconds: int = Field(
        1200, description="Minimum amount between Objects in a Track for a Lag/Lead Event"
    )
    max_lag_lead_duration_seconds: int = Field(
        2700, description="Maximum between Objects in a Track for a Lag/Lead Event"
    )
    max_potential_duplicate_time_diff_seconds: int = Field(
        30,
        description="Max amount of time between colocated points to qualify a potential duplicate")
    # loiter_event_name: str = Field("LoiterEvent", description="Name prefix for OMSB Loiter Event Nodes")
    # loiter_event_node_iri: str = Field("http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct",
    #                                description="OMSB Loiter Event Node IRI")
    # loiter_relationship_iri: str = Field("http://purl.obolibrary.org/obo/BFO_0000197",
    #                                      description="OMSB Loiter Event Node to Track Relationship IRI")
    # loiter_event_node_attribute_iri: str = Field("https://foundry.ai.mil/ontology/4901-001/hasCoordinates",
    #                                              description="OMSB Loiter Event Node Geo Attribute IRI")
    # potential_duplicate_relationship_name: str = Field("Potential Duplicate",
    #                                                    description="Name for OMSB Potential Duplicate")
    # cotravel_event_name: str = Field("Cotravel", description="Name prefix for OMSB Cotravel Event Nodes")
    # lag_lead_event_name: str = Field("LagLead", description="Name prefix for OMSB LagLead Event Nodes")
    # cotravel_event_node_iri: str = Field("http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct",
    #                                description="OMSB Cotravel Event Node IRI")
    # cotravel_relationship_iri: str = Field("http://purl.obolibrary.org/obo/BFO_0000197",
    #                                      description="OMSB Cotravel Event Node to Track Relationship IRI")
    # cotravel_event_node_attribute_iri: str = Field("https://foundry.ai.mil/ontology/4901-001/hasCoordinates",
    #                                              description="OMSB Cotravel Event Node Geo Attribute IRI")
    # cotravel_track_to_event_relation_name: str = Field("inheres in",
    #                                              description="OMSB Cotravel Event Node to Track Relationship Name")

    # Similar Track Settings
    n_tracks: int = Field(5, description="Number of similar tracks to return")
    within_meters: float = Field(3000.0, description="Used to define the search space for potential similar tracks")

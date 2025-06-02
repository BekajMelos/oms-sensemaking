from pydantic import BaseModel, Field


class GeospatialSensemakerConfig(BaseModel):
    valid_observed_threshold_seconds: int = Field(
        900, description="Threshold for amount of between Track Point Observations"
    )
    loiter_geohash: int = Field(5, description="Geohash for Loiter Sensemaker")
    cotravel_geohash: int = Field(5, description="Geohash for Cotravel Sensemaker")
    similar_tracks_geohash: int = Field(5, description="Geohash for Similar Tracks Sensemaker")

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
        30, description="Max amount of time between colocated points to qualify a potential duplicate"
    )

    # Similar Track Settings
    within_meters: float = Field(3000.0, description="Used to define the search space for potential similar tracks")

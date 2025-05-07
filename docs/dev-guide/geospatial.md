# Geospatial Sensemaker Config Settings


##### Sensemaker Settings

| Variable Name                                       | Example                                                                                           | Description                                                    |
|:----------------------------------------------------|:--------------------------------------------------------------------------------------------------|:---------------------------------------------------------------|
| `valid_observed_threshold_seconds`                  | `900`                                                                                             | Threshold for amount of between Track Point Observations       |
| `loiter_geohash`                                       | `5`                                                                                               | Geohash for Loiter Sensemaker                                                    |
| `cotravel_geohash`                                       | `5`                                                                                               | Geohash for Cotravel Sensemaker                                                    |
| `similar_tracks_geohash`                                       | `5`                                                                                               | Geohash for Similar Tracks Sensemaker                                                    |
| `loiter_min_time`                                   | `900`                                                                                             | Minimum amount of time for a valid Loiter Event                |
| `min_cotravel_duration_seconds`                     | `1200`                                                                                            | Minimum between Objects in a Track for a Cotravel Event        |
| `min_lag_lead_duration_seconds`                     | `1200`                                                                                            | Minimum amount between Objects in a Track for a Lag/Lead Event |
| `max_lag_lead_duration_seconds`                     | `2700`                                                                                            | Maximum between Objects in a Track for a Lag/Lead Event        |
| `max_potential_duplicate_time_diff_seconds`                                     | `30`                                                                                          | Max amount of time between colocated points to qualify a potential duplicate   |
| `within_meters`                                     | `3000.0`                                                                                          | Used to define the search space for potential similar tracks   |
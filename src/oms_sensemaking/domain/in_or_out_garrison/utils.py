from geopy.distance import geodesic

from oms_sensemaking.config import SETTINGS


def in_garrison(object_latlon: list, garrison_latlon: list) -> bool:
    """
    Determine whether an observed node is within the garrison boundary.
    Computes the geodesic distance (in kilometers) between the object's location
    and the garrison's location. Returns True if the object lies within the
    configured garrison distance threshold, False otherwise.
    :param object_latlon: [lat, lon] coordinates of the observed object
    :param garrison_latlon: [lat, lon] coordinates of the garrison
    """
    distance = geodesic(object_latlon, garrison_latlon).kilometers
    return distance < SETTINGS.garrison_distance_kilometers

import json
import logging

from oms_sdk.generated.generated_graphql_client import AttributeQuery, NodeQuery, PageParams

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.iw.sensemakers.geofence_observable import GeofenceObservable
from oms_sensemaking.iw.sensemakers.min_distance_observable import MinDistanceObservable
from oms_sensemaking.iw.sensemakers.search_observable import SearchObservable
from oms_sensemaking.iw.sensemakers.status_observable import StatusObservable

LOGGER: logging.Logger = logging.getLogger(__name__)

QUERY_CLASS_MAP = {
    "geofence": GeofenceObservable,
    "minDistance": MinDistanceObservable,
    "status": StatusObservable,
    "search": SearchObservable,
}


def process_observables():
    """Main function to process all observables."""
    oms_client = OmsCrudTool()

    # fetch all observables
    observable_query = NodeQuery(tags=["observable"], pageParams=PageParams(pageSize=1))
    observables_result = oms_client.get_nodes(observable_query)

    if not observables_result.data:
        LOGGER.info("No observables found")
        return

    for observable_node in observables_result.data:
        # get Config attribute
        config_attributes = oms_client.get_attributes(
            AttributeQuery(
                nodeIds=[observable_node.id], attributeIris=[SETTINGS.iw_settings.observable_config_attribute_iri]
            )
        )

        if not config_attributes.data:
            LOGGER.error(f"No config found for observable {observable_node.id}")
            continue

        # determine observable type and create appropriate instance
        try:
            config_data = json.loads(config_attributes.data[0].attributeValue)
            query_type = config_data.get("queryType")

            if query_type in QUERY_CLASS_MAP:
                observable = QUERY_CLASS_MAP[query_type](**config_data)
            else:
                LOGGER.error(f"Unsupported query type for observable {observable_node.id}: {query_type}")
                continue

            # set instance properties
            observable.initialize(observable_node.id, oms_client)

            # process the observable
            observable.update_data()

        except Exception as e:
            LOGGER.error(f"Error processing observable {observable_node.id}: {e}")


if __name__ == "__main__":
    process_observables()

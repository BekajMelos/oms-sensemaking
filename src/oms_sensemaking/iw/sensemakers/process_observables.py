import json
import logging
from typing import Dict, Type

from oms_sdk.generated.generated_graphql_client import AttributeQuery, NodeQuery, PageParams

from oms_sensemaking.clients.instances import oms_crud_tool
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.iw.sensemakers.observables.base_observable import BaseObservable, ObservableQueryType

from . import GeofenceObservable, SearchObservable

LOGGER: logging.Logger = logging.getLogger(__name__)

QUERY_CLASS_MAP: Dict[ObservableQueryType, Type[BaseObservable]] = {
    ObservableQueryType.geofence: GeofenceObservable,
    ObservableQueryType.search: SearchObservable,
}


def process_observables():
    """Main function to process all observables."""

    # fetch all observables
    observable_query = NodeQuery(
        tags=["observable"], pageParams=PageParams(pageSize=SETTINGS.iw_settings.max_observables_to_process)
    )
    observables_result = None
    try:
        observables_result = oms_crud_tool.get_nodes(observable_query)
    except Exception as e:
        LOGGER.error("Failed to fetch observables")
        LOGGER.error(e)
        return

    if not observables_result.data:
        LOGGER.info("No observables found")
        return

    for observable_node in observables_result.data:
        # get Config attribute
        config_attributes = oms_crud_tool.get_attributes(
            AttributeQuery(
                nodeIds=[observable_node.id], attributeIris=[SETTINGS.iw_settings.observable_config_attribute_iri]
            )
        )

        if not config_attributes.data:
            LOGGER.error("No config found for observable %s", observable_node.id)
            continue

        # determine observable type and create appropriate instance
        try:
            config_data = json.loads(config_attributes.data[0].attributeValue)
            query_type = config_data.get("queryType")

            if query_type in QUERY_CLASS_MAP:
                observable = QUERY_CLASS_MAP[query_type](**config_data)
            else:
                LOGGER.error("Unsupported query type for observable %s: %s", observable_node.id, query_type)
                continue

            # set instance properties
            observable.initialize(observable_node.id, oms_crud_tool)

            # process the observable
            observable.update_data()

        except Exception as e:
            LOGGER.error("Error processing observable %s: %s", observable_node.id, e)


if __name__ == "__main__":
    process_observables()

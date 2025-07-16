import json
from pprint import pprint

from oms_sdk.generated.generated_graphql_client import (
    AttributeQuery,
    NodeQuery,
    PageParams
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.iw.sensemakers.geofence_observable import GeofenceObservable
from oms_sensemaking.iw.sensemakers.min_distance_observable import MinDistanceObservable
from oms_sensemaking.iw.sensemakers.search_observable import SearchObservable
from oms_sensemaking.iw.sensemakers.status_observable import StatusObservable

QUERY_CLASS_MAP = {
    "geofence": GeofenceObservable,
    "minDistance": MinDistanceObservable,
    "status": StatusObservable,
    "search": SearchObservable,
}

def process_observables():
    """Main function to process all observables."""
    oms_client = OmsCrudTool()

    print("1!!!!!")

    # fetch all observables
    observable_query = NodeQuery(tags=["observable"], pageParams=PageParams(pageSize=1))
    observables_result = oms_client.get_nodes(observable_query)
    print('or d')
    pprint(observables_result.data)
    print()

    if not observables_result.data:
        print("No observables found")
        return

    for observable_node in observables_result.data:

        # get Config attribute
        config_attributes = oms_client.get_attributes(
            AttributeQuery(
                nodeIds=[observable_node.id], attributeIris=[SETTINGS.iw_settings.observable_config_attribute_iri]
            )
        )

        if not config_attributes.data:
            print(f"No config found for observable {observable_node.id}")
            continue

        # determine observable type and create appropriate instance
        try:
            config_data = json.loads(config_attributes.data[0].attributeValue)
            print('cg')
            pprint(config_data)
            print()

            query_type = config_data.get("queryType")

            if query_type in QUERY_CLASS_MAP:
                observable = QUERY_CLASS_MAP[query_type](**config_data)
            else:
                print(f"Unspuported query type: {query_type}")
                continue

            # set instance properties
            observable.initialize(observable_node.id, oms_client)

            # process the observable
            observable.update_data()

        except Exception as e:
            print(f"Error processing observable {observable_node.id}: {e}")


if __name__ == "__main__":
    oms_client = OmsCrudTool()
    print("1!!!!!!!")
    observable_query = NodeQuery(tags=["observable"], pageParams=PageParams(pageSize=1))
    print("2!!!!!!!")
    observables = oms_client.get_nodes(observable_query)
    print("3!!!!!!!")
    # process_observables()

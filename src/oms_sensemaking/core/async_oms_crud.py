from oms_sdk import get_generated_async_graphql_client
from oms_sdk.generated.generated_async_graphql_client import (
    Client,
    CreateActivityInput,
    CreateNodeInput,
    CreateObservationInput,
    CreateOriginatorInput,
    CreateProviderInput,
    CreateSourceInput,
)

from oms_sensemaking.config import SETTINGS


class AsyncOmsCrudTool:
    """Tool for using OMS_SDK CRUD operations"""

    def __init__(self, user_dn: str | None = None) -> None:
        self.oms_client: Client = get_generated_async_graphql_client(
            url=SETTINGS.omsb_url,
            user_dn=user_dn or SETTINGS.user_dn,
            cert_path=SETTINGS.cert_path,
            key_path=SETTINGS.key_path,
            pkcs12_path=SETTINGS.pkcs12_path,
            pkcs12_password=SETTINGS.pkcs12_password,
        )

    def create_node(self, node_input: CreateNodeInput):
        """
        Publish the Nodes to OMS
        :param node_input: a  CreateNodeInput object
        """
        # 1. for each node, publish it to OMS
        return self.oms_client.create_node(node_input)

    def create_observation(self, observation_input: CreateObservationInput):
        """
        Publish the Observations to OMS
        """
        return self.oms_client.create_observation(observation_input)

    def create_activity(self, activity_input: CreateActivityInput):
        """
        Publish the activity to oms
        :param activity_input: a CreateActivityInput object
        """
        # 1. for each activity, publish it to OMS
        return self.oms_client.create_activity(activity_input)

    def create_originator(self, originator_input: CreateOriginatorInput):
        return self.oms_client.create_originator(originator_input)

    def create_provider(self, provider_input: CreateProviderInput):
        return self.oms_client.create_provider(provider_input)

    def create_source(self, source_input: CreateSourceInput):
        return self.oms_client.create_source(source_input)

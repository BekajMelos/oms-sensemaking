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
from oms_sdk.profiled_transport import ProfiledAsyncHTTPTransport, async_add_request_time_header

from oms_sensemaking.config import SETTINGS


class AsyncAtomsCrudTool:
    """Tool for using OMS_SDK CRUD operations"""

    def __init__(self, user_dn: str | None = None) -> None:
        self._atoms_client: Client = get_generated_async_graphql_client(
            url=SETTINGS.omsb_url,
            user_dn=user_dn or SETTINGS.user_dn,
            cert_path=SETTINGS.cert_path,
            key_path=SETTINGS.key_path,
            pkcs12_path=SETTINGS.pkcs12_path,
            pkcs12_password=SETTINGS.pkcs12_password,
            ssl_cert_file_path=SETTINGS.atoms_cacert_path,
            verify_ssl=SETTINGS.atoms_client_verify_ssl,
            transport=ProfiledAsyncHTTPTransport,
            event_hooks={"request": [async_add_request_time_header]},
        )

    def create_node(self, node_input: CreateNodeInput):
        """
        Publish the Nodes to ATOMS
        :param node_input: a  CreateNodeInput object
        """
        # 1. for each node, publish it to ATOMS
        return self._atoms_client.create_node(node_input)

    def create_observation(self, observation_input: CreateObservationInput):
        """
        Publish the Observations to ATOMS
        """
        return self._atoms_client.create_observation(observation_input)

    def create_activity(self, activity_input: CreateActivityInput):
        """
        Publish the activity to atoms
        :param activity_input: a CreateActivityInput object
        """
        # 1. for each activity, publish it to ATOMS
        return self._atoms_client.create_activity(activity_input)

    def create_originator(self, originator_input: CreateOriginatorInput):
        return self._atoms_client.create_originator(originator_input)

    def create_provider(self, provider_input: CreateProviderInput):
        return self._atoms_client.create_provider(provider_input)

    def create_source(self, source_input: CreateSourceInput):
        return self._atoms_client.create_source(source_input)

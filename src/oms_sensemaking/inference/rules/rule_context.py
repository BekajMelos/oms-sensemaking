from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.node import NodeNode
from oms_sdk.generated.generated_graphql_client.relationship import RelationshipRelationship
from oms_sdk.generated.generated_graphql_client.source import SourceSource
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation
from oms_sdk.generated.generated_graphql_client.activity import ActivityActivity

class RuleContext:
    """
    Map inputs for the rules into well defined models, this gives us direct access
    to properties in the rules for a variety of object types
    """

    def __init__(self, **kwargs) -> None:
        self.attribute: AttributeAttribute = kwargs.get("attribute")
        self.relationship: RelationshipRelationship = kwargs.get("relationship")
        self.source: SourceSource = kwargs.get("source")
        self.node: NodeNode = kwargs.get("node")
        self.observation: ObservationObservation = kwargs.get("observation")
        self.activity: ActivityActivity = kwargs.get("observation")

    def get_properties(self):
        return vars(self)

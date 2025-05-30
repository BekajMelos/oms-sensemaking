import logging
from itertools import product

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
)

from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER = logging.getLogger(__name__)
class Criteria:
    '''
    A class for initializing the attribute IRI criteria of a
    specific node when checking for its duplicates
    '''
    def __init__(self, iris: list[str]):
        self.iris = iris

    def without(self, target_iri: str) -> list[str]:
        '''
        Helper method that returns a list of IRIs

        :return: A list[str] of IRIs that exclude a
        target IRI (current attribute being examined)
        '''
        return [iri for iri in self.iris if iri != target_iri]

    def __len__(self):
        '''
        :return: return the length of the list of criteria IRIs
        '''
        return len(self.iris)

class AttributeCombinations:
    '''
    A class for creating a list of attribute combinations of a node that may
    match with other nodes' attributes (duplicate objects)
    '''
    def __init__(self, attribute: AttributeAttribute, oms_crud_tool: OmsCrudTool,
                 duplicate_object_iris: dict[str,list[str]]) -> None:
        """Create a new instance of AttributeCombinations creator class."""
        self.attribute = attribute
        self.oms_crud_tool = oms_crud_tool
        self.duplicate_object_iris = duplicate_object_iris

    def gather(self, node_iri: str) -> list[list[AttributeAttribute]]:
        '''
        A method used to gather various combinations of attributes associated
        with a node that may match other nodes' attributes

        :return: A valid list of lists of attributes where the inner lists are combinations
        of attributes which may match to other nodes' attributes
        '''

        identifiers = self.duplicate_object_iris[node_iri]
        criteria = Criteria(identifiers)
        current_iri = self.attribute.attributeIri
        other_iris = criteria.without(current_iri)

        # default to current attribute
        groups = [[self.attribute]]

        if len(criteria) > 1:
            other_attrs = self.oms_crud_tool.get_node_attribute_by_iri(self.attribute.nodeId, other_iris)
            groups.extend(self.attribute_combinator(other_attrs))

        return [g for g in groups if len(g) == len(criteria)]

    def attribute_combinator(self, other_attrs: list[AttributeAttribute]) -> list[list[AttributeAttribute]]:
        '''
        A helper function used to create various combinations of attributes associated
        with a node

        :param other_attrs: A list of attributes associated with a node that
        exclude the current attribute being examined
        :return: A list of lists of attributes where the inner lists are different
        combinations of attributes associated with a node
        '''
        attr_dict: dict[str, list[AttributeAttribute]] = {}

        for attr in other_attrs:
            attr_dict.setdefault(attr.attributeIri, []).append(attr)

        attr_groups = list(attr_dict.values())
        valid_combinations = []

        for combo in product(*attr_groups):
            group = [self.attribute] + list(combo)
            if all(attr.attributeValue != "" for attr in group):
                valid_combinations.append(group)

        return valid_combinations

"""Object Minimums Sensemakers."""

import logging

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
)

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker

LOGGER = logging.getLogger(__name__)


class ObjectMinimums(Sensemaker):
    """
    A sensemaker for grading object completeness.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial object minimums sensemaker

    """

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of ResolutionSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {}
        self.oms_crud_tool = oms_crud_tool

    def process_data(self, attribute_of_node: AttributeAttribute, config: dict | None = None):
        """
        Determine the completeness of an ATOMS node based off its various related components

        :param class_object: The object to analyze.
        :return: Grade
        """
        LOGGER.info("Running Object Minimums Sensemaker")
        return []

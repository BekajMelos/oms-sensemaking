"""Military Symbol Sensemakers."""

import logging
from typing import Any, List

from oms_sdk.generated.generated_graphql_client import (
    NodeNode,
)

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker

LOGGER = logging.getLogger(__name__)


class MilSymbolSensemaker(Sensemaker):
    """
    A sensemaker for detecting duplicate nodes in omsb.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial "mil_symbol" algorithm implementation.

    """

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of MilSymbolSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {}
        self.oms_crud_tool = oms_crud_tool


    def process_data(self, oms_node: NodeNode) -> Any:
        """
        Update a Node's symbol code based on its attributes and metadata

        :param oms_node: The node to analyze.
        :return: List of Mil Symbol Code updates
        """
        LOGGER.info("Running MilSymbol Sensemaker")

        results: List = []

        return results

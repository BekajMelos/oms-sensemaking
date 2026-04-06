"""COCOM Traversal Sensemakers."""

import logging
from typing import Any

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker

LOGGER = logging.getLogger(__name__)


class COCOMTraversalSensemaker(Sensemaker):
    """
    A sensemaker for identifying COCOM boundary traversals.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial COCOM traversal sensemaker

    """

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of COCOMTraversal sensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.oms_crud_tool = oms_crud_tool

    def process_data(self, data: Any, config: Any | None = None) -> Any:
        """
        Determine if a Node has crossed a COCOM boundary line

        currently still a dummy function
        """
        return []

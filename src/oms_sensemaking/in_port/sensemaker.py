"""Object Standards Sensemakers."""

import logging

from oms_sensemaking.clients.ontology_client import OntologyService
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker

LOGGER = logging.getLogger(__name__)


class InPort(Sensemaker):
    """
    A sensemaker for determining when an object is near a port location.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial in port sensemaker

    """

    def __init__(
        self,
        oms_crud_tool: OmsCrudTool,
        ontology_service: OntologyService,
    ) -> None:
        """Create a new instance of InPort sensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.oms_crud_tool = oms_crud_tool
        self.ontology_service = ontology_service

    def process_data(
        self,
    ):
        """
        Determine when an object is near a port location.
        """
        return

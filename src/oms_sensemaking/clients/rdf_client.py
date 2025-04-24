import logging

from pydantic import UUID4

from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER: logging.Logger = logging.getLogger(__name__)

class RDFClient:
    def get_rdf_from_id(self, obj_id: UUID4, oms_crud_tool: OmsCrudTool):
        """Return service information."""
        LOGGER.info(f"RDF API request from object: {obj_id}")
        try:
            node = oms_crud_tool.get_node(obj_id)
            return node
        except Exception as e:
            LOGGER.error(repr(e))
            return None

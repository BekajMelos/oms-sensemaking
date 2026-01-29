import logging
from typing import Callable

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.input_types import (
    NodeQuery,
    PageParams,
)

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER: logging.Logger = logging.getLogger(__name__)


class HealthChecker:
    """Get health status of dependencies"""

    _healthy = "healthy"
    _unhealthy = "Unable to communicate with"

    def get_oms_health(self, oms_crud_tool: OmsCrudTool):
        LOGGER.debug("Checking ATOMS health")
        try:
            query = NodeQuery(pageParams=PageParams(pageSize=1))
            oms_crud_tool.get_nodes(query)
            return self._healthy
        except Exception as e:
            LOGGER.error(repr(e))
            return f"{self._unhealthy} ATOMS"

    def get_db_health(self, ping_db: Callable[[], bool]):
        LOGGER.debug("Checking DB health")
        try:
            ok = ping_db()
            return self._healthy if ok else f"{self._unhealthy} DB Service"
        except Exception as e:
            LOGGER.error(repr(e))
            return f"{self._unhealthy} DB Service"

    def get_aac_health(self, aac_service: AacClient):
        LOGGER.debug("Checking AAC Service health")
        try:
            aac_service.get_acm_rollup([{"ACM": DEFAULT_ACM}])
            return self._healthy
        except Exception as e:
            LOGGER.error(repr(e))
            return f"{self._unhealthy} AAC Service"

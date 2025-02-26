"""Provides a Sensemaker base class."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import httpx
from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from oms_sdk.generated.generated_graphql_client import (
    CreateAttributeCreateAttribute,
    CreateAttributeInput,
    CreateNodeCreateNode,
    CreateNodeInput,
    CreateRelationshipCreateRelationship,
    CreateRelationshipInput,
)

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.models.sensemaking import Finding, FindingType

LOGGER: logging.Logger = logging.getLogger(__name__)


def jsonify(data):
    """Recursively converts all data types in a JSON object to strings."""

    if isinstance(data, dict):
        return {k: jsonify(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [jsonify(item) for item in data]
    elif isinstance(data, WKBElement):
        return to_shape(data).wkt
    elif hasattr(data, "to_dict"):
        return jsonify(data.to_dict())
    elif isinstance(data, (int, float, bool)) or data is None:
        return data
    else:
        return str(data)


class SensemakerPublisher(ABC):
    def __init__(self) -> None:
        """Create a new instance of the Publisher."""
        super().__init__()

    @abstractmethod
    def publish(self, data: Any, results: Any) -> Any:
        """Publish output to OMS"""
        raise NotImplementedError


class NoOpPublisher(SensemakerPublisher):
    def publish(self, data: Any, results: Any) -> Any:
        """Don't do anything"""
        pass


class OmsPublisher(SensemakerPublisher):
    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of the Publisher."""
        super().__init__()
        self.oms_crud_tool = oms_crud_tool
        self.node_uuid_list: list[str] = []  # in-order list of unpublished node IDs
        self.node_id_mapping: dict[str, str] = {}  # map unpublished node IDs to published node IDs

    def publish(self, data: Any, results: Any) -> None:
        self.node_uuid_list = []  # Make sure old lists doesn't persist between publishes
        self.node_id_mapping = {}  # Make sure old mappings don't persist between publishes
        self.publish_nodes(self.format_nodes(data, results))
        self.publish_relationships(self.format_relationships(data, results))
        self.publish_attributes(self.format_attributes(data, results))

    def format_nodes(self, data, results) -> list[CreateNodeInput]:
        raise NotImplementedError

    def publish_nodes(self, formatted_nodes: list[CreateNodeInput]) -> list[CreateNodeCreateNode]:
        published_nodes = []
        for index, node in enumerate(formatted_nodes):
            published_node = self.oms_crud_tool.create_node(node_input=node)
            self.node_id_mapping[self.node_uuid_list[index]] = published_node.id
            published_nodes.append(published_node)
        return published_nodes

    def format_relationships(self, data, results) -> list[CreateRelationshipInput]:
        raise NotImplementedError

    def publish_relationships(
        self, formatted_relationships: list[CreateRelationshipInput]
    ) -> list[CreateRelationshipCreateRelationship]:
        return self.oms_crud_tool.publish_relationships(formatted_relationships)

    def format_attributes(self, data, results) -> list[CreateAttributeInput]:
        raise NotImplementedError

    def publish_attributes(
        self, formatted_attributes: list[CreateAttributeInput]
    ) -> list[CreateAttributeCreateAttribute]:
        return self.oms_crud_tool.publish_attributes(formatted_attributes)


@dataclass
class FindingBase(ABC):
    FINDING_TYPE: FindingType

    def to_dict(self) -> dict:
        """Return a dictionary representation of the object."""
        return jsonify(asdict(self))

    def get_acm(self) -> dict:
        """Return the acm for this object"""
        raise NotImplementedError


class Sensemaker(ABC):
    """Abstract Sensemaker base class."""

    def __init__(self, *args, **kwargs) -> None:
        """Create a new instance of the sensemaker."""
        super().__init__()
        self.name: str = self.__class__.__name__
        self.config: dict = {}
        self.lock: Lock = Lock()
        self.publisher: SensemakerPublisher = NoOpPublisher()

        #: The algorithm version [MAJOR, MINOR, PATCH]. Subclasses should set this to acknowledge notable changes.
        self.version: tuple[int | str, int | str, int | str] = (0, 0, 0)
        self.executed_at: datetime

    def setup(self):
        """
        Pre-execution setup function.

        Subclasses should override this function to provide any custom setup
        needed before the sensemaker is executed.
        """
        LOGGER.debug("Initializing %s", self.__class__)

    def teardown(self):
        """
        Post-execution teardown function.

        Subclasses should override this function to provide any custom logic
        needed after the sensemaker is executed.
        """
        LOGGER.debug("Cleaning up after %s", self.__class__)

    @property
    def version_string(self) -> str:
        """Return the algorithm version as a semantic version string."""
        return ".".join(map(str, self.version))

    def execute(self, data: Any) -> Any:
        """
        Execute the Sensemaker.

        This method handles calling the ``setup`` and ``teardown`` methods
        before and after the ``process_data`` method. It will then write the
        findings returned to the oms_sensemaking db. It is unlikely that this
        method needs to be overridden in a subclass, but if it is, some care
        will be needed to ensure that the expectation of those two methods
        being called is not broken.
        """
        try:
            self.setup()
            with self.lock:
                self.executed_at = datetime.now(tz=timezone.utc)
                LOGGER.info(f"Running {self.name} {self.version_string}")
                results: Any = self.process_data(data)
                self.save_findings(results)
                try:
                    if results:
                        self.publisher.publish(data, results)
                except httpx.RequestError as exc:
                    LOGGER.exception(f"An error occurred while requesting {exc.request.url!r}.")

                LOGGER.info(f"Sensemaker {self.name} {self.version_string} completed")
        finally:
            self.teardown()

        return results

    def save_findings(self, finding_objects: Iterable[FindingBase]) -> None:
        """
        Write the findings to the sensemaking db

        :param finding_objects: List of finding objects to write as findings
        """

        if finding_objects:
            LOGGER.info(f"Saving findings from {self.name} {self.version_string} to DB")

        findings: list = []
        for finding_object in finding_objects:
            finding = Finding(
                acm=finding_object.get_acm(),
                algorithm_name=self.name,
                algorithm_version=f"{self.version[0]}.{self.version[1]}.{self.version[2]}",
                algorithm_configuration=self.config,
                executed_at=self.executed_at,
                finding_type=finding_object.FINDING_TYPE,
                finding_data=finding_object.to_dict(),
                oms_version=SETTINGS.omsb_version,
                published_at=datetime.now(tz=timezone.utc),
            )
            findings.append(finding)

        with db_session() as db:
            db.add_all(findings)
            db.commit()

    @abstractmethod
    # TODO: enforce common return format
    # def process_data(self, data: Any) -> Iterable[FindingBase]:
    def process_data(self, data: Any) -> Any:
        """
        Process data.

        This method provides the implementation of the sensemaker's business
        logic. Subclasses must override this method.
        """
        raise NotImplementedError()

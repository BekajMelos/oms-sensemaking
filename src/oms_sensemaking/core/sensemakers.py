"""Provides a Sensemaker base class."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from functools import cached_property
from threading import Lock
from typing import Any, Iterable, List, Tuple

import httpx
from oms_sdk.generated.generated_graphql_client.client import Client

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.models.sensemaking import Finding, FindingType

LOGGER: logging.Logger = logging.getLogger(__name__)


def jsonify(data):
    """Recursively converts all data types in a JSON object to strings."""

    if isinstance(data, dict):
        return {k: jsonify(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [jsonify(item) for item in data]
    else:
        return str(data)


class SensemakerPublisher(ABC):

    def __init__(self) -> None:
        """Create a new instance of the Publisher."""
        super().__init__()

    @abstractmethod
    def publish(self, *args, **kwargs) -> None:
        """Publish output to OMS"""
        raise NotImplementedError


class NoOpPublisher(SensemakerPublisher):

    def publish(self, *args, **kwargs) -> None:
        """Don't do anything"""
        pass


class OmsPublisher(SensemakerPublisher):

    def __init__(self, oms_client: Client) -> None:
        """Create a new instance of the Publisher."""
        super().__init__()
        self.oms_client: Client = oms_client


class FindingBase(ABC):

    FINDING_TYPE: FindingType

    def to_dict(self) -> dict:
        return jsonify(self.__dict__)

    @cached_property
    @abstractmethod
    def acm(self) -> dict:
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
        self.version: Tuple[int | str, int | str, int | str] = (0, 0, 0)
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
                results: Any = self.process_data(data)
                self.save_findings(results)
                try:
                    self.publisher.publish(data, results)
                except httpx.RequestError as exc:
                    LOGGER.exception(f"An error occurred while requesting {exc.request.url!r}.")
        finally:
            self.teardown()

        return results

    def save_findings(self, finding_objects: Iterable[FindingBase]) -> None:
        """
        Write the findings to the sensemaking db

        :param finding_objects: List of finding objects to write as findings
        """
        LOGGER.debug("Saving Findings to DB")
        findings: List = []
        for finding_object in finding_objects:
            finding = Finding(
                acm=finding_object.acm,
                algorithm_name=self.name,
                algorithm_version=f"{self.version[0]}.{self.version[1]}.{self.version[2]}",
                algorithm_configuration=self.config,
                executed_at=self.executed_at,
                finding_type=finding_object.FINDING_TYPE,
                finding_data=finding_object.to_dict(),
                oms_version=SETTINGS.omsb_version,
                published_at=datetime.now(tz=timezone.utc)
            )
            findings.append(finding)

        with db_session() as db:
            db.add_all(findings)
            db.commit()


    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """
        Process data.

        This method provides the implementation of the sensemaker's business
        logic. Subclasses must override this method.
        """
        raise NotImplementedError()

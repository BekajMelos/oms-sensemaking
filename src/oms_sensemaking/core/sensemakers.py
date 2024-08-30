"""Provides a Sensemaker base class."""

import logging
from abc import ABC, abstractmethod
from threading import Lock
from typing import TypeVar

LOGGER: logging.Logger = logging.getLogger(__name__)

T = TypeVar("T")
SENSEMAKER_RESULT_TYPE = TypeVar("SENSEMAKER_RESULT_TYPE")


class Sensemaker(ABC):
    """Abstract Sensemaker base class."""

    def __init__(self) -> None:
        """Create a new instance of the sensemaker."""
        super().__init__()
        self.lock: Lock = Lock()

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

    def execute(self, data: T) -> SENSEMAKER_RESULT_TYPE:
        """
        Execute the Sensemaker.

        This method handles calling the ``setup`` and ``teardown`` methods
        before and after the ``process_data`` method. It is unlikely that this
        method needs to be overridden in a subclass, but if it is, some care
        will be needed to ensure that the expectation of those two methods
        being called is not broken.
        """
        try:
            self.setup()
            with self.lock:
                results: SENSEMAKER_RESULT_TYPE = self.process_data(data)
        finally:
            self.teardown()

        return results

    @abstractmethod
    def process_data(self, data: T) -> SENSEMAKER_RESULT_TYPE:
        """
        Process data.

        This method provides the implementation of the sensemaker's business
        logic. Subclasses must override this method.
        """
        raise NotImplementedError()

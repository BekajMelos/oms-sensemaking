import logging
from abc import ABC, abstractmethod
from typing import Dict

LOGGER = logging.getLogger(__name__)


class BaseRule(ABC):
    """
    Simple definition Rule that all other rules must be based on
    """

    def __init__(self, name: str):
        self.name = name
        assert name, "Attempted to create a rule without a name"

    def get_name(self) -> str:
        """
        Get the name of the rule
        """

        return self.name

    def execute(self, input: Dict[str, any]):
        """
        Execution space for the rule

        :param input: Generic object used to evaluate and execute the rule
        """

        LOGGER.debug(f"Executing Rule {self.get_name()}")
        if self.evaluate(input):
            self.action(input)
        return

    @abstractmethod
    def evaluate(self, input: Dict[str, any]) -> bool:
        """
        Determine if the input's properties justify running the action method

        :param input: Generic object used to test conditions
        """

        raise NotImplementedError

    @abstractmethod
    def action(self, input: Dict[str, any]):
        """
        The command to run when this rule's conditions are met

        :param input: Generic object used in the command
        """

        raise NotImplementedError

    def _evaluate(self, input: Dict[str, any]) -> bool:
        """
        Pre running step for the evaluate method
        """

        LOGGER.info(f"Evaluating Rule {self.get_name()}")
        return self.evaluate(input)

    def _action(self, input: Dict[str, any]) -> bool:
        """
        Pre running step for the action method
        """

        LOGGER.info(f"Executing Action for Rule {self.get_name()}")
        return self.action(input)

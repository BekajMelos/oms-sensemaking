import logging
from abc import ABC, abstractmethod

from oms_sensemaking.inference.rules.rule_context import RuleContext

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

    def execute(self, input: RuleContext):
        """
        Execution space for the rule

        :param input: Generic object used to evaluate and execute the rule
        """

        LOGGER.debug(f"Executing Rule {self.get_name()}")
        if self._evaluate(input):
            self._action(input)
        return

    @abstractmethod
    def evaluate(self, input: RuleContext) -> bool:
        """
        Determine if the input's properties justify running the action method

        :param input: Generic object used to test conditions
        """

        raise NotImplementedError

    @abstractmethod
    def action(self, input: RuleContext):
        """
        The command to run when this rule's conditions are met

        :param input: Generic object used in the command
        """

        raise NotImplementedError

    def _evaluate(self, input: RuleContext) -> bool:
        """
        Pre running step for the evaluate method
        """

        LOGGER.info(f"Evaluating Rule {self.get_name()}")
        return self.evaluate(input)

    def _action(self, input: RuleContext) -> bool:
        """
        Pre running step for the action method
        """

        LOGGER.info(f"Executing Action for Rule {self.get_name()}")
        return self.action(input)

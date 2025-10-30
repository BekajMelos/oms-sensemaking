import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Tuple

from oms_sensemaking.core.sensemakers import FindingWriter, SensemakerMetaData
from oms_sensemaking.inference.rules.rule_context import RuleContext

LOGGER = logging.getLogger(__name__)


class BaseRule(ABC, SensemakerMetaData):
    """
    Simple definition Rule that all other rules must be based on
    """

    def __init__(self, name: str = ""):
        self.name: str = name if name else self.__class__.__name__
        self.config: dict = {}

        #: The algorithm version [MAJOR, MINOR, PATCH]. Subclasses should set this to acknowledge notable changes.
        self.version: Tuple[int | str, int | str, int | str] = (0, 0, 0)
        self.executed_at: datetime
        self._finding_writer = FindingWriter()

    def get_name(self) -> str:
        """
        Get the name of the rule
        """

        return self.name

    def execute(self, rule_context: RuleContext):
        """
        Execution space for the rule

        :param rule_context: Generic object used to evaluate and execute the rule
        """

        LOGGER.debug("Executing Rule %s with rule_context %s", self.get_name(), rule_context)
        if not self._has_action_already_ran(rule_context) and self._evaluate(rule_context):
            self._action(rule_context)
        return

    @abstractmethod
    def has_action_already_ran(self, rule_context: RuleContext) -> bool:
        """
        Determine if the action has already happened in a previous run

        :param rule_context: Generic object used to test conditions
        """

        raise NotImplementedError

    @abstractmethod
    def evaluate(self, rule_context: RuleContext) -> bool:
        """
        Determine if the rule_context's properties justify running the action method

        :param rule_context: Generic object used to test conditions
        """

        raise NotImplementedError

    @abstractmethod
    def action(self, rule_context: RuleContext):
        """
        The command to run when this rule's conditions are met

        :param rule_context: Generic object used in the command
        """

        raise NotImplementedError

    def _has_action_already_ran(self, rule_context: RuleContext) -> bool:
        """
        Pre running step for the action_already_taken method
        """

        LOGGER.info("Determining if action already taken for rule %s", self.get_name())
        return self.has_action_already_ran(rule_context)

    def _evaluate(self, rule_context: RuleContext) -> bool:
        """
        Pre running step for the evaluate method
        """

        LOGGER.info("Evaluating Rule %s", self.get_name())
        return self.evaluate(rule_context)

    def _action(self, rule_context: RuleContext) -> bool:
        """
        Pre running step for the action method
        """

        LOGGER.info("Executing Action for Rule %s", self.get_name())
        self.executed_at = datetime.now(tz=timezone.utc)
        return self.action(rule_context)

    @property
    def version_string(self) -> str:
        """Return the algorithm version as a semantic version string."""
        return "v" + ".".join(map(str, self.version))

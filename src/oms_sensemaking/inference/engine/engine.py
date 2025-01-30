import logging

from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext

LOGGER = logging.getLogger(__name__)


class Engine:
    """
    Executor of a set of rules
    """

    def __init__(self) -> None:
        self._rules: list[BaseRule] = []

    def add_rule(self, rule: BaseRule):
        """
        Add a rule to the list of rules the engine executes

        :param rule: The rule to add
        """

        LOGGER.debug(f"Adding {rule.get_name()}")
        self._rules.append(rule)

    def execute_rules(self, rule_context: RuleContext):
        """
        Execute the set of rules using the given rule_context

        :param rule_context: The rule_context to test rule conditions with.  There is
        A LOT of flexibility in this, while everything is simple, just
        use the basic oms type (eg. attribute, node, relationship, etc...
        so rules can use rule_context.attribute, rule_context.node, rule_context.relationship,
        rule_context.etc...)
        """

        self._log_input_ids(rule_context)

        for rule in self._rules:
            rule.execute(rule_context)

    def _log_input_ids(self, rule_context: RuleContext):
        """
        Determine the ids sent as part of the rule_context

        :param rule_context: The object to analyze for id fields
        """

        ids = []

        props = rule_context.get_properties()

        for prop in props.values():
            if prop and prop.id:
                ids.append(prop.id)

        LOGGER.info(f"Executing rules for rule_context with ids {ids}")

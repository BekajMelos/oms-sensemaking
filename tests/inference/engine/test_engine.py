from pytest_mock import MockerFixture

from oms_sensemaking.inference.engine.engine import Engine
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext


class RuleHelper(BaseRule):
    def evaluate(self, input):
        return True

    def action(self, input):
        return

    def has_action_already_ran(self, input):
        return False


class Data:
    def __init__(self, id):
        self.id = id


def test_engine_execution(mocker: MockerFixture):
    test_rule = RuleHelper("test rule")
    mock = mocker.patch.object(test_rule, "execute")
    engine = Engine()
    engine.add_rule(test_rule)

    input = RuleContext(attribute=Data("abc"), node=Data("123"))

    engine.execute_rules(input)
    mock.assert_called_once_with(input)

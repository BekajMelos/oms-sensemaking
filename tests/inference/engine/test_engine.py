from oms_sensemaking.inference.engine.engine import Engine
from oms_sensemaking.inference.rules.base import BaseRule


class RuleHelper(BaseRule):
    def evaluate(self, input):
        return True

    def action(self, input):
        return


def test_engine_execution(mocker):
    test_rule = RuleHelper("test rule")
    mock = mocker.patch.object(test_rule, "execute")
    engine = Engine()
    engine.add_rule(test_rule)
    engine.execute_rules({})
    mock.assert_called_once()

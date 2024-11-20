from pytest_mock import MockerFixture

from oms_sensemaking.inference.rules.base_rule import BaseRule


class BaseRuleHelper(BaseRule):
    def evaluate(self, input):
        return True

    def action(self, input):
        return

    def has_action_already_ran(self, input):
        return True


def test_has_action_already_ran(mocker: MockerFixture):
    test_rule = BaseRuleHelper("already ran true test")
    mocker.patch.object(test_rule, "has_action_already_ran").return_value = True
    test_rule.execute({})
    mock = mocker.patch.object(test_rule, "action")
    mock.assert_not_called()


def test_evaluate_true_execution(mocker: MockerFixture):
    test_rule = BaseRuleHelper("evaluate true test")
    mock = mocker.patch.object(test_rule, "action")
    mocker.patch.object(test_rule, "has_action_already_ran").return_value = False
    test_rule.execute({})
    mock.assert_called_once()


def test_evaluate_false_execution(mocker: MockerFixture):
    test_rule = BaseRuleHelper("evaluate false test")
    mocker.patch.object(test_rule, "evaluate").return_value = False
    mocker.patch.object(test_rule, "has_action_already_ran").return_value = False
    mock = mocker.patch.object(test_rule, "action")
    test_rule.execute({})
    mock.assert_not_called()

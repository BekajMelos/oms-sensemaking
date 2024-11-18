from oms_sensemaking.inference.rules.attribute_has_name import AttributeHasName


class Engine:
    def __init__(self):
        self._rules: list[AttributeHasName] = []

    def add_rule(self, rule: AttributeHasName):
        print(f"adding {rule.get_name()}")
        self._rules.append(rule)

    def execute_rules(self, input):
        for rule in self._rules:
            rule.execute(input)

from abc import ABC, abstractmethod


class BaseRule(ABC):
    def __init__(self, name: str):
        self.name = name
        assert name, "Attempted to create a rule without a name"

    def get_name(self) -> str:
        return self.name

    def execute(self, input):
        print(f"Running {self.name}")
        if self.evaluate(input):
            self.action(input)
        return

    @abstractmethod
    def evaluate(self, input) -> bool:
        raise NotImplementedError

    @abstractmethod
    def action(self, input):
        raise NotImplementedError

import logging
from typing import Any, Iterable

from oms_sensemaking.core.sensemakers import FindingBase, Sensemaker
from oms_sensemaking.inference.engine.engine import Engine
from oms_sensemaking.inference.rules.add_has_name_attribute import AddHasNameAttribute
from oms_sensemaking.inference.rules.rule_context import RuleContext

LOGGER = logging.getLogger(__name__)


class InferenceSensemaker(Sensemaker):
    def __init__(self):
        """Create a new instance of InferenceSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.config = {"rules": [AddHasNameAttribute("AddHasNameAttribute")]}
        self.engine = Engine()

        for rule in self.config.get("rules", []):
            self.engine.add_rule(rule)

    def process_data(self, data: Any) -> Iterable[FindingBase]:
        """
        Process data.

        This method provides the implementation of the sensemaker's business
        logic. Subclasses must override this method.
        """
        LOGGER.info("Running the Inference Sensemaker")
        LOGGER.debug(f"processing data {data}")

        # TODO Properly build out RuleContext args
        self.engine.execute_rules(RuleContext(attribute=data))

        # TODO Figure out what to do with findings, process_data is called in
        # the base class and is expected to return findings, but the important
        # config+algorithm data for Inference is in the rules

        # return data
        # purposefully do not return any results for now
        LOGGER.debug(f"finished processing data {data}")
        return []

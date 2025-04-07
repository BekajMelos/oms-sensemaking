import logging
from typing import Iterable

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.sensemakers import FindingBase, Sensemaker
from oms_sensemaking.inference.engine.engine import Engine
from oms_sensemaking.inference.rules.add_garrison_attribute import AddOutOfGarrisonAttribute
from oms_sensemaking.inference.rules.add_has_name_attribute import AddHasNameAttribute
from oms_sensemaking.inference.rules.in_out_garrison import InOrOutOfGarrison
from oms_sensemaking.inference.rules.incursions import Incursion
from oms_sensemaking.inference.rules.rule_context import RuleContext

LOGGER = logging.getLogger(__name__)


class InferenceSensemaker(Sensemaker):
    def __init__(self):
        """Create a new instance of InferenceSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.config = {"rules": [AddHasNameAttribute("AddHasNameAttribute"),
                                 Incursion("Incursion"),
                                 InOrOutOfGarrison("InOrOutOfGarrison")]}
        self.engine = Engine()
        rule_mappings = {
            "toggle_add_garrison_rule": AddOutOfGarrisonAttribute("AddOutOfGarrisonAttribute"),
            "toggle_add_has_name_rule": AddHasNameAttribute("AddHasNameAttribute"),
            "toggle_incursion_rule": Incursion("Incursion"),
        }
        for setting_name, rule in rule_mappings.items():
            if getattr(SETTINGS, setting_name, False):  # Check if toggle is True
                self.config["rules"].append(rule)
                self.engine.add_rule(rule)

    def process_data(self, data: RuleContext) -> Iterable[FindingBase]:
        """
        Process data.

        This method provides the implementation of the sensemaker's business
        logic. Subclasses must override this method.
        """

        self.engine.execute_rules(data)

        # process_data is called in the base class and is expected to return findings,
        # but the important config+algorithm data for Inference is in the rules
        # the rules self publish and save findings, there's nothing more to do here

        return []

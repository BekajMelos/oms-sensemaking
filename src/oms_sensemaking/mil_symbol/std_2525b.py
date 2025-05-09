"""Military Symbol Standard 2525B"""

import logging
from typing import Optional

from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C

LOGGER = logging.getLogger(__name__)

class MilSymbol2525B(MilSymbol2525C):
    """
    Inherits from MilSymbol2525C

    Difference between classes 2525B and 2525C is held in affiliation enrichment
    """
    def enrich_affiliation(self, affiliation_attr: Optional[AttributeAttribute]) -> None:
        """Update Affilation

        :param affiliation_attr: Attribute for the affiliation
        :return: None
        """

        if affiliation_attr:
            node_standard_identity = affiliation_attr.attributeValue
            for code, standard_identity_list in self.settings["MIL_SYMBOL_2525B"]["STANDARD_IDENTITY_LISTS"].items():
                if node_standard_identity.lower() in standard_identity_list:
                    self.update_code(self.MIL_SYM_2525C_STD_IDENTITY_IDX, code)
                    self.source_ids.put((1, affiliation_attr.sourceId))
                    self.acms.append(affiliation_attr.acm)
                    LOGGER.debug(f'Updated std identity: {code} b/c {node_standard_identity}')
                    break

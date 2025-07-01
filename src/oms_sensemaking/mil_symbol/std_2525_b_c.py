"""Class For Shared Methods and Properties between 2525C and 2525B"""

import logging
from abc import abstractmethod
from typing import List, Optional

from oms_sdk.generated.generated_graphql_client import AttributeAttribute, NodeNode

from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol

LOGGER = logging.getLogger(__name__)


class MilSymbol2525BandC(MilSymbol):
    """
    Parent class for 2525B and 2525C.

    2525B and 2525C inherit all properties of this class
    and overwrite affiliation.
    """

    UNKNOWN_DIMENSION_CODE = "Z"

    # E.g.  SUZP------*****
    MIL_SYM_2525_B_C_STD_IDENTITY_IDX = 1
    MIL_SYM_2525_B_C_DIMENSION_IDX = 2
    MIL_SYM_2525_B_C_STATUS_IDX = 3
    MIL_SYM_2525_B_C_SYM_MOD_IDX_0 = 10
    MIL_SYM_2525_B_C_SYM_MOD_IDX_1 = 11
    MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX = 14
    MIL_SYM_2525_B_C_PLACEHOLDERS = ["-", "*"]

    @property
    @abstractmethod
    def code_type_config(self) -> str:
        """
        Subclasses define their own config type
        """

    @property
    def formatted_code(self) -> str:
        "Return the formatted code"
        return self.code

    def enrich(
        self,
        affiliation_attr: Optional[AttributeAttribute],
        oms_node: NodeNode,
        ancestor_iris: List[str],
        status_attr: Optional[AttributeAttribute],
        echelon_attr: Optional[AttributeAttribute],
    ) -> None:
        """Enrich the code given node attribute data

        :param affiliation_attr: Optional Attribute for the affiliation
        :param oms_node: Node we are processing
        :param ancestor_iris: Node's ancestor iri list
        :param status_attr: Optional Attribute for the status
        """

        self.enrich_affiliation(affiliation_attr)
        self.enrich_dimension(oms_node, ancestor_iris)
        self.enrich_status(status_attr)
        self.enrich_echelon(echelon_attr)

    def enrich_affiliation(self, affiliation_attr: Optional[AttributeAttribute]) -> None:
        """Update Affilation

        :param affiliation_attr: Attribute for the affiliation
        :return: None
        """

        if affiliation_attr:
            node_standard_identity = affiliation_attr.attributeValue
            # Default to 2525C config settings for affiliation, gets overwritten in child classes
            for code, standard_identity_list in self.settings[self.code_type_config]["STANDARD_IDENTITY_LISTS"].items():
                if node_standard_identity.lower() in standard_identity_list:
                    self.update_code(self.MIL_SYM_2525_B_C_STD_IDENTITY_IDX, code)
                    self.source_ids.put((1, affiliation_attr.sourceId))
                    self.acms.append(affiliation_attr.acm)
                    LOGGER.debug(f"Updated std identity: {code} b/c {node_standard_identity}")
                    break

    def enrich_dimension(self, oms_node: NodeNode, ancestor_iris: List[str]) -> None:
        """Update Dimension

        Use node's IRIs to update list. If not found and is Unknown, use ancestor IRIs

        :param iri: Node's class iri
        :return: None
        """

        def update_dimension(current_iri: str) -> bool:
            """if iri matches dimension rules, update code

            :param current_iri: Iri to check
            :return: boolean indicating whether update was made or not
            """
            current_iri = current_iri.lower()
            for code, dimension_iris in self.settings[self.code_type_config]["DIMENSION_IRIS"].items():
                dimension_iris = [dimension_iri.lower() for dimension_iri in dimension_iris]
                if current_iri in dimension_iris:
                    self.update_code(self.MIL_SYM_2525_B_C_DIMENSION_IDX, code)
                    self.acms.append(oms_node.acm)
                    LOGGER.debug(f"Updated dimension: {code} b/c {current_iri}")
                    return True
            return False

        if update_dimension(oms_node.classIri):
            return

        dimension_code = self.code[self.MIL_SYM_2525_B_C_DIMENSION_IDX]
        code_is_unknown = dimension_code == self.UNKNOWN_DIMENSION_CODE
        if code_is_unknown:
            LOGGER.debug(f"Dimension code is still unknown. Checking ancestor iris: {ancestor_iris}")
            for iri in ancestor_iris:
                if update_dimension(iri):
                    return

    def enrich_status(self, status_attr: Optional[AttributeAttribute]) -> None:
        """Update Status

        :param status_attr: Attribute for the status
        :return: None
        """

        if status_attr:
            status = status_attr.attributeValue
            for code, status_list in self.settings[self.code_type_config]["STATUS_LISTS"].items():
                if status.lower() in status_list:
                    self.update_code(self.MIL_SYM_2525_B_C_STATUS_IDX, code)
                    self.source_ids.put((2, status_attr.sourceId))
                    self.acms.append(status_attr.acm)
                    LOGGER.debug(f"Updated status: {code} b/c {status}")
                    break

    def enrich_echelon(self, echelon_attr: Optional[AttributeAttribute]) -> None:
        """
        Update echelon (symbol modifer)

        :param echelon_attr: Attribute for echelon
        :return: None
        """
        current_placeholder = None
        pre_enriched_sym_mod = (
            self.formatted_code[self.MIL_SYM_2525_B_C_SYM_MOD_IDX_0]
            + self.formatted_code[self.MIL_SYM_2525_B_C_SYM_MOD_IDX_1]
        )
        for placeholder in self.MIL_SYM_2525_B_C_PLACEHOLDERS:
            if placeholder in pre_enriched_sym_mod:
                current_placeholder = placeholder
                break
        if echelon_attr:
            echelon = echelon_attr.attributeValue
            for code, echelon_list in self.settings[self.code_type_config]["SYMBOL_MODIFIER_LISTS"].items():
                if echelon.lower() in echelon_list:
                    if current_placeholder and any(c in code for c in self.MIL_SYM_2525_B_C_PLACEHOLDERS):
                        code = "".join(
                            current_placeholder if char in self.MIL_SYM_2525_B_C_PLACEHOLDERS else char for char in code
                        )
                    self.update_code(self.MIL_SYM_2525_B_C_SYM_MOD_IDX_0, code[0])
                    self.update_code(self.MIL_SYM_2525_B_C_SYM_MOD_IDX_1, code[1])
                    self.source_ids.put((3, echelon_attr.sourceId))
                    self.acms.append(echelon_attr.acm)
                    LOGGER.debug(f"Updated echelon: {code} b/c {echelon}")
                    break

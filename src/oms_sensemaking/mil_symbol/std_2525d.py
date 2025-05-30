"""Military Symbol Standard 2525D."""
import logging
from typing import Dict, List, Optional

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    NodeNode,
)

from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol

LOGGER = logging.getLogger(__name__)


class MilSymbol2525D(MilSymbol):
    """Class for MIL-STD-2525D format SIDCs"""

    UNKNOWN_DIMENSION_CODE = "00"

    # E.g.  10000100000000000000
    MIL_SYM_2525D_CONTEXT_IDX = 2
    MIL_SYM_2525D_STD_IDENTITY_IDX = 3
    MIL_SYM_2525D_DIMENSION_IDX_0 = 4
    MIL_SYM_2525D_DIMENSION_IDX_1 = 5
    MIL_SYM_2525D_STATUS_IDX = 6


    def __init__(self, code: str, settings: Dict) -> None:
        super().__init__(code, settings)
        self.code = code.replace("-", "")

    @property
    def formatted_code(self) -> str:
        "Return the code formatted into dash separated sections"

        return (f"{self.code[0:2]}-{self.code[2]}-{self.code[3]}-{self.code[4:6]}-{self.code[6]}-"
                f"{self.code[7]}-{self.code[8:10]}-{self.code[10:16]}-{self.code[16:18]}-{self.code[18:20]}")

    def enrich(self,
               context_attr: Optional[AttributeAttribute],
               affiliation_attr: Optional[AttributeAttribute],
               oms_node: NodeNode,
               ancestor_iris: List[str],
               status_attr: Optional[AttributeAttribute]) -> None:
        """Enrich the code given node attribute data

        :param context_attr: Optional Attribute for the context
        :param affiliation_attr: Optional Attribute for the affiliation
        :param iri: Node's class iri
        :param ancestor_iris: Node's ancestor iri list
        :param status_attr: Optional Attribute for the status
        """

        self.enrich_context(context_attr)
        self.enrich_affiliation(affiliation_attr)
        self.enrich_dimension(oms_node, ancestor_iris)
        self.enrich_status(status_attr)

    def enrich_context(self, context_attr: Optional[AttributeAttribute]) -> None:
        """Update Context

        :param context_attr: Attribute for the context
        :return: None
        """

        if context_attr:
            context = context_attr.attributeIri
            for code, context_list in self.settings["MIL_SYMBOL_2525D"]["CONTEXT_LISTS"].items():
                # TODO ignore case?
                if context in context_list:
                    self.update_code(self.MIL_SYM_2525D_CONTEXT_IDX, code)
                    self.source_ids.put((3, context_attr.sourceId))
                    self.acms.append(context_attr.acm)
                    LOGGER.debug(f'Updated context: {code} b/c {context}')
                    break

    def enrich_affiliation(self, affiliation_attr: Optional[AttributeAttribute]) -> None:
        """Update Affilation

        :param affiliation_attr: Attribute for the affiliation
        :return: None
        """

        if affiliation_attr:
            node_standard_identity = affiliation_attr.attributeValue
            for code, standard_identity_list in self.settings["MIL_SYMBOL_2525D"]["STANDARD_IDENTITY_LISTS"].items():
                if node_standard_identity.lower() in standard_identity_list:
                    self.update_code(self.MIL_SYM_2525D_STD_IDENTITY_IDX, code)
                    self.source_ids.put((1, affiliation_attr.sourceId))
                    self.acms.append(affiliation_attr.acm)
                    LOGGER.debug(f'Updated std identity: {code} b/c {node_standard_identity}')
                    break

    def enrich_dimension(self, oms_node: NodeNode, ancestor_iris: List[str]) -> None:
        """Update Dimension

        Use node's IRIs to update list. If not found and is Unknown, use ancestor IRIs

        :param oms_node: Node being processed
        :param iri: Node's class iri
        :return: None
        """

        def update_dimension(current_iri: str) -> bool:
            """if iri matches dimension rules, update code

            :param current_iri: Iri to check
            :return: boolean indicating whether update was made or not
            """
            current_iri = current_iri.lower()
            for code, dimension_iris in self.settings["MIL_SYMBOL_2525D"]["DIMENSION_IRIS"].items():
                dimension_iris = [dimension_iri.lower() for dimension_iri in dimension_iris]
                if current_iri in dimension_iris:
                    self.update_code(self.MIL_SYM_2525D_DIMENSION_IDX_0, code[0])
                    self.update_code(self.MIL_SYM_2525D_DIMENSION_IDX_1, code[1])
                    self.acms.append(oms_node.acm)
                    LOGGER.debug(f'Updated dimension: {code} b/c {current_iri}')
                    return True
            return False

        if update_dimension(oms_node.classIri):
            return

        dimension_code = self.code[self.MIL_SYM_2525D_DIMENSION_IDX_0] + self.code[self.MIL_SYM_2525D_DIMENSION_IDX_0]
        code_is_unknown = dimension_code == self.UNKNOWN_DIMENSION_CODE
        if code_is_unknown:
            LOGGER.debug(f'Dimension code is still unknown. Checking ancestor iris: {ancestor_iris}')
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
            for code, status_list in self.settings["MIL_SYMBOL_2525D"]["STATUS_LISTS"].items():
                if status.lower() in status_list:
                    self.update_code(self.MIL_SYM_2525D_STATUS_IDX, code)
                    self.source_ids.put((2, status_attr.sourceId))
                    self.acms.append(status_attr.acm)
                    LOGGER.debug(f'Updated status: {code} b/c {status}')
                    break

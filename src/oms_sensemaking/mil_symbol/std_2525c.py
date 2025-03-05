"""Military Symbol Standard 2525C"""

import logging
from typing import List, Optional

from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol

LOGGER = logging.getLogger(__name__)


class MilSymbol2525C(MilSymbol):

    UNKNOWN_DIMENSION_CODE = "Z"

    # E.g.  SUZP------*****
    MIL_SYM_2525C_STD_IDENTITY_IDX = 1
    MIL_SYM_2525C_DIMENSION_IDX = 2
    MIL_SYM_2525C_STATUS_IDX = 3


    @property
    def formatted_code(self) -> str:
        "Return the formatted code"
        return self.code

    def enrich(self,
               affiliation_attr: Optional[AttributeAttribute],
               iri: str,
               ancestor_iris: List[str],
               status_attr: Optional[AttributeAttribute]) -> None:
        """Enrich the code given node attribute data

        :param affiliation_attr: Optional Attribute for the affiliation
        :param iri: Node's class iris current iri and parent list
        :param status_attr: Optional Attribute for the status
        """

        self.enrich_affiliation(affiliation_attr)
        self.enrich_dimension(iri, ancestor_iris)
        self.enrich_status(status_attr)

    def enrich_affiliation(self, affiliation_attr: Optional[AttributeAttribute]) -> None:
        """Update Affilation

        :param affiliation_attr: Attribute for the affiliation
        :return: None
        """

        # TODO there could be multiple IRIs for affiliation

        if affiliation_attr:
            node_standard_identity = affiliation_attr.attributeValue
            for code, standard_identity_list in self.settings["MIL_SYMBOL_2525C"]["STANDARD_IDENTITY_LISTS"].items():
                if node_standard_identity.lower() in standard_identity_list:
                    self.update_code(self.MIL_SYM_2525C_STD_IDENTITY_IDX, code)
                    self.source_ids.put((1, affiliation_attr.sourceId))
                    LOGGER.debug(f'Updated std identity: {code} b/c {node_standard_identity}')
                    break

        # TODO handle if no affiliation and derivative node
        # look for parent relationship http://schema.dia.mil/DefenseIntelligenceCoreOntology/controlledBy

    def enrich_dimension(self, iri: str, ancestor_iris: List[str]) -> None:
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
            for code, dimension_iris in self.settings["MIL_SYMBOL_2525C"]["DIMENSION_IRIS"].items():
                dimension_iris = [dimension_iri.lower() for dimension_iri in dimension_iris]
                if current_iri in dimension_iris:
                    self.update_code(self.MIL_SYM_2525C_DIMENSION_IDX, code)
                    LOGGER.debug(f'Updated dimension: {code} b/c {current_iri}')
                    return True
            return False

        if update_dimension(iri):
            return

        dimension_code = self.code[self.MIL_SYM_2525C_DIMENSION_IDX]
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
            for code, status_list in self.settings["MIL_SYMBOL_2525C"]["STATUS_LISTS"].items():
                if status.lower() in status_list:
                    self.update_code(self.MIL_SYM_2525C_STATUS_IDX, code)
                    self.source_ids.put((2, status_attr.sourceId))
                    LOGGER.debug(f'Updated status: {code} b/c {status}')
                    break

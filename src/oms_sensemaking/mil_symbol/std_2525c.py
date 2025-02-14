"""Military Symbol Standard 2525C"""

import logging
from typing import Optional

from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol

LOGGER = logging.getLogger(__name__)


class MilSymbol2525C(MilSymbol):

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
               status_attr: Optional[AttributeAttribute]) -> None:
        """Enrich the code given node attribute data

        :param affiliation_attr: Optional Attribute for the affiliation
        :param iri: Node's class iri
        :param status_attr: Optional Attribute for the status
        """

        self.enrich_affiliation(affiliation_attr)
        self.enrich_dimension(iri)
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

    def enrich_dimension(self, iri: str) -> None:
        """Update Dimension

        :param iri: Node's class iri
        :return: None
        """

        # TODO I think this should check all parent iris for a match

        # TODO ignore case?
        for code, value in self.settings["MIL_SYMBOL_2525C"]["DIMENSION_IRIS"].items():
            if iri in value:
                self.update_code(self.MIL_SYM_2525C_DIMENSION_IDX, code)
                LOGGER.debug(f'Updated dimension: {code} b/c {iri}')
                break

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

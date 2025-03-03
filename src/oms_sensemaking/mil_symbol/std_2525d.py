"""Military Symbol Standard 2525D."""
import logging
from typing import Dict, Optional

from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol

LOGGER = logging.getLogger(__name__)


class MilSymbol2525D(MilSymbol):

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
               iri: str,
               status_attr: Optional[AttributeAttribute]) -> None:
        """Enrich the code given node attribute data

        :param context_attr: Optional Attribute for the context
        :param affiliation_attr: Optional Attribute for the affiliation
        :param iri: Node's class iri
        :param status_attr: Optional Attribute for the status
        """

        self.enrich_context(context_attr)
        self.enrich_affiliation(affiliation_attr)
        self.enrich_dimension(iri)
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
                    LOGGER.debug(f'Updated std identity: {code} b/c {node_standard_identity}')
                    break

        # TODO if no affiliation and derivative node
        # look for parent relationship http://schema.dia.mil/DefenseIntelligenceCoreOntology/controlledBy

    def enrich_dimension(self, iri: str) -> None:
        """Update Dimension

        :param iri: Node's class iri
        :return: None
        """

        # TODO I think this should check all parent iris for a match

        # TODO ignore case?
        for code, dimension_list in self.settings["MIL_SYMBOL_2525D"]["DIMENSION_IRIS"].items():
            if iri in dimension_list:
                self.update_code(self.MIL_SYM_2525D_DIMENSION_IDX_0, code[0])
                self.update_code(self.MIL_SYM_2525D_DIMENSION_IDX_1, code[1])
                LOGGER.debug(f'Updated dimension: {code} b/c {iri}')
                break

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
                    LOGGER.debug(f'Updated status: {code} b/c {status}')
                    break

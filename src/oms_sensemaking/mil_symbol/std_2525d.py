"""Military Symbol Standard 2525D."""
import logging
from typing import Optional

from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol

LOGGER = logging.getLogger(__name__)


class MilSymbol2525D(MilSymbol):

    # Context Settings
    CONTEXT_LISTS = {
        "0": SETTINGS.mil_symbol_settings.is_reality_context_iris,
        "1": SETTINGS.mil_symbol_settings.is_exercise_context_iris,
        "2": SETTINGS.mil_symbol_settings.is_simulation_context_iris
    }

    # Standard Identity Settings
    PENDING_STANDARD_IDENTITIES = ["pending"]
    UNKNOWN_STANDARD_IDENTITIES = ["unknown"]
    ASSUMED_FRIENDLY_STANDARD_IDENTITIES = ["assumed friend", "assumed friendly"]
    FRIENDLY_STANDARD_IDENTITIES = ["friend", "friendly"]
    NEUTRAL_STANDARD_IDENTITIES = ["neutral"]
    SUSPECT_STANDARD_IDENTITIES = ["suspect", "joker", "assumed hostile"]
    HOSTILE_STANDARD_IDENTITIES = ["hostile", "faker"]

    STANDARD_IDENTITY_LISTS = {
        "0": PENDING_STANDARD_IDENTITIES,
        "1": UNKNOWN_STANDARD_IDENTITIES,
        "2": ASSUMED_FRIENDLY_STANDARD_IDENTITIES,
        "3": FRIENDLY_STANDARD_IDENTITIES,
        "4": NEUTRAL_STANDARD_IDENTITIES,
        "5": SUSPECT_STANDARD_IDENTITIES,
        "6": HOSTILE_STANDARD_IDENTITIES
    }

    # Dimension Settings
    # Should include high level IRIs and exceptions
    DIMENSION_IRIS = {
        "00": ["http://purl.obolibrary.org/obo/BFO_0000040"],
        "01": [
            "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            "http://omsb/test/Plane",
            "http://omsb/test/Helicopter",
            "http://omsb/test/Apache"
            ],
        "02": [],  # air missile
        "05": ["http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft"],
        "06": [],  # space missile
        "10": [
            "http://www.ontologyrepository.com/CommonCoreOntologies/GroundVehicle",
            "http://omsb/test/Tank",
            "http://omsb/test/LAV",
            ],
        "11": ["http://schema.dia.mil/DefenseIntelligenceCoreOntology/CivilianInstallation"],
        "15": [],  # land equipiment
        "20": [
            "http://schema.dia.mil/DefenseIntelligenceCoreOntology/Installation",
            "http://schema.dia.mil/DefenseIntelligenceCoreOntology/MilitaryInstallation"
            ],
        "25": [],  # control measure
        "30": ["http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"],
        "35": ["http://omsb/test/Submarine"],  # subsurface
        "36": [],  # mine warfare
        "40": [],  # activities
        "45": [],  # meteorological - atmospheric
        "46": [],  # meteorological - oceanographic
        "47": [],  # meteorological - space
        "50": [],  # signals intelligence - space
        "51": [],  # signals intelligence - air
        "52": [],  # signals intelligence - land
        "53": [],  # signals intelligence - surface
        "54": [],  # signals intelligence - subsurface
        "60": [],  # cyberspace
    }

    # Status Settings
    PRESENT_STATUSES = ["present"]
    SUSPECT_STATUSES = ["suspect", "planned", "anticipated"]
    READY_STATUSES = ["ready", "fully capable"]
    DAMAGED_STATUSES = ["damaged"]
    DESTROYED_STATUSES = ["destroyed"]
    FULL_TO_CAPACITY_STATUSES = ["full to capacity"]

    STATUS_LISTS = {
        "0": PRESENT_STATUSES,
        "1": SUSPECT_STATUSES,
        "2": READY_STATUSES,
        "3": DAMAGED_STATUSES,
        "4": DESTROYED_STATUSES,
        "5": FULL_TO_CAPACITY_STATUSES
    }

    # E.g.  10000100000000000000
    MIL_SYM_2525D_CONTEXT_IDX = 2
    MIL_SYM_2525D_STD_IDENTITY_IDX = 3
    MIL_SYM_2525D_DIMENSION_IDX_0 = 4
    MIL_SYM_2525D_DIMENSION_IDX_1 = 5
    MIL_SYM_2525D_STATUS_IDX = 6


    def __init__(self, code: str) -> None:
        super().__init__(code)
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
            for code, context_list in self.CONTEXT_LISTS.items():
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
            for code, standard_identity_list in self.STANDARD_IDENTITY_LISTS.items():
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
        for code, dimension_list in self.DIMENSION_IRIS.items():
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
            for code, status_list in self.STATUS_LISTS.items():
                if status.lower() in status_list:
                    self.update_code(self.MIL_SYM_2525D_STATUS_IDX, code)
                    self.source_ids.put((2, status_attr.sourceId))
                    LOGGER.debug(f'Updated status: {code} b/c {status}')
                    break

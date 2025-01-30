"""Military Symbol Standard 2525C"""

import logging
from typing import Optional

from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol

LOGGER = logging.getLogger(__name__)


class MilSymbol2525C(MilSymbol):

    # Standard Identity Settings
    PENDING_STANDARD_IDENTITIES = ["pending"]
    UNKNOWN_STANDARD_IDENTITIES = ["unknown"]
    ASSUMED_FRIENDLY_STANDARD_IDENTITIES = ["assumed friend", "assumed friendly"]
    FRIENDLY_STANDARD_IDENTITIES = ["friend", "friendly"]
    NEUTRAL_STANDARD_IDENTITIES = ["neutral"]
    SUSPECT_STANDARD_IDENTITIES = ["suspect", "assumed hostile"]
    HOSTILE_STANDARD_IDENTITIES = ["hostile"]
    EXERCISE_PENDING_STANDARD_IDENTITIES = ["exercise pending"]
    EXERCISE_UNKNOWN_STANDARD_IDENTITIES = ["exercise unknown"]
    EXERCISE_ASSUMED_FRIEND_STANDARD_IDENTITIES = ["exercise assumed friend", "exercise assumed friendly"]
    EXERCISE_FRIEND_STANDARD_IDENTITIES = ["exercise friend", "exercise friendly"]
    EXERCISE_NEUTRAL_STANDARD_IDENTITIES = ["exercise neutral"]
    JOKER_STANDARD_IDENTITIES = ["joker"]
    FAKER_STANDARD_IDENTITIES = ["faker"]

    STANDARD_IDENTITY_LISTS = {
        "P": PENDING_STANDARD_IDENTITIES,
        "U": UNKNOWN_STANDARD_IDENTITIES,
        "A": ASSUMED_FRIENDLY_STANDARD_IDENTITIES,
        "F": FRIENDLY_STANDARD_IDENTITIES,
        "N": NEUTRAL_STANDARD_IDENTITIES,
        "S": SUSPECT_STANDARD_IDENTITIES,
        "H": HOSTILE_STANDARD_IDENTITIES,
        "G": EXERCISE_PENDING_STANDARD_IDENTITIES,
        "W": EXERCISE_UNKNOWN_STANDARD_IDENTITIES,
        "M": EXERCISE_ASSUMED_FRIEND_STANDARD_IDENTITIES,
        "D": EXERCISE_FRIEND_STANDARD_IDENTITIES,
        "L": EXERCISE_NEUTRAL_STANDARD_IDENTITIES,
        "J": JOKER_STANDARD_IDENTITIES,
        "K": FAKER_STANDARD_IDENTITIES,
    }

    # Dimension Settings
    # Should include high level IRIs and exceptions
    DIMENSION_IRIS = {
        "P": ["http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft"],
        "A": [
            "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            "http://omsb/test/Plane",
            "http://omsb/test/Helicopter",
            "http://omsb/test/Apache"
        ],
        "G": [
            "http://www.ontologyrepository.com/CommonCoreOntologies/GroundVehicle",
            "http://omsb/test/Tank",
            "http://omsb/test/LAV",
            "http://schema.dia.mil/DefenseIntelligenceCoreOntology/CivilianInstallation",
            "http://schema.dia.mil/DefenseIntelligenceCoreOntology/Installation",
            "http://schema.dia.mil/DefenseIntelligenceCoreOntology/MilitaryInstallation",
        ],
        "S": ["http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"],
        "U": ["http://omsb/test/Submarine"],
        "F": [],  # Currently Unsupported
        "X": [],  # Currently Unsupported
        "Z": ["http://purl.obolibrary.org/obo/BFO_0000040"],  # unknown
    }

    # Status Settings
    ANTICIPATED_STATUSES = ["anticipated", "planned"]
    PRESENT_STATUSES = ["present"]  # TODO is this units only?
    FULLY_CAPABLE_STATUSES = ["fully capable"]
    DAMAGED_STATUSES = ["damaged"]
    DESTROYED_STATUSES = ["destroyed"]
    FULL_TO_CAPACITY_STATUSES = ["full to capacity"]

    STATUS_LISTS = {
        "A": ANTICIPATED_STATUSES,
        "P": PRESENT_STATUSES,
        "C": FULLY_CAPABLE_STATUSES,
        "D": DAMAGED_STATUSES,
        "X": DESTROYED_STATUSES,
        "F": FULL_TO_CAPACITY_STATUSES,
    }

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
            for code, standard_identity_list in self.STANDARD_IDENTITY_LISTS.items():
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
        for code, value in self.DIMENSION_IRIS.items():
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
            for code, status_list in self.STATUS_LISTS.items():
                if status.lower() in status_list:
                    self.update_code(self.MIL_SYM_2525C_STATUS_IDX, code)
                    self.source_ids.put((2, status_attr.sourceId))
                    LOGGER.debug(f'Updated status: {code} b/c {status}')
                    break

"""Object Standards ATOMS Publisher."""

import logging
from datetime import datetime

from oms_sdk.generated.generated_graphql_client import (
    CreateObjectStandardsInput,
    NodesNodesData,
    ObjectStandardsObjectStandardsData,
    UpdateObjectStandardsInput,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.object_standards.object_standards_models import (
    ObjectStandardsGrade,
)

LOGGER = logging.getLogger(__name__)


class ObjectStandardsATOMSPublisher:
    def __init__(self, oms_crud_tool: OmsCrudTool):
        self.oms_crud_tool = oms_crud_tool

    def publish_results_to_atoms(
        self,
        node: NodesNodesData,
        existing: list[ObjectStandardsObjectStandardsData],
        rolled_up_acm: dict,
        grade: ObjectStandardsGrade,
        summary: str,
        object_standard_calculation_time: datetime,
    ):
        """
        This is a helper function used to publish Object Standards results to ATOMS.
        If there is a matching (based off version), existing Object Standard, update it.
        If there is no existing Object Standard, create it.

        :param node: The class object that is being processed throughout the Sensemaker
        :param attributes: The attributes connected to the class object
        :param relationships: The relationships connected to the class object
        :param rolled_up_acm: rollup ACM of all objects used to calculate grade
        :param grade: The Object Standards grade
        :param summary: The summary string of the Object Standards result
        :param object_standard_calculation_time: The time recorded for when the grade was calculated
        :return: N/A
        """
        if existing:
            # Grab first result; only one Object Standard per version
            existing_object_standard = existing[0]
            update_object_standards_input = UpdateObjectStandardsInput(
                id=existing_object_standard.id,
                acm=rolled_up_acm,
                summary=summary,
                score=grade.float_score,
                violations=grade.violations,
                compliantObjects=grade.compliant_fields,
                timestamp=object_standard_calculation_time,
                standardsVersion=SETTINGS.object_standards_settings.playbook_version,
            )
            LOGGER.info(f"Updating Object Standards results for node: {node.id}")
            self.oms_crud_tool.update_object_standards(update_object_standards_input)
        else:
            object_standards_input = CreateObjectStandardsInput(
                acm=rolled_up_acm,
                tags=SETTINGS.object_standards_settings.tags,
                nodeId=node.id,
                summary=summary,
                score=grade.float_score,
                violations=grade.violations,
                compliantObjects=grade.compliant_fields,
                timestamp=object_standard_calculation_time,
                standardsVersion=SETTINGS.object_standards_settings.playbook_version,
            )
            LOGGER.info(f"Publishing Object Standards results for node: {node.id}")
            self.oms_crud_tool.create_object_standards(object_standards_input)

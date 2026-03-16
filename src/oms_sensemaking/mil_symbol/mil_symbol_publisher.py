import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
    Confidence,
    CreateAttributeInput,
    CreateMilSymAttributes,
    CreateMilSymAttributesMilSymAttr1,
    CreateMilSymAttributesMilSymAttr2,
    CreateMilSymAttributesMilSymAttr3,
    NodeNode,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase
from oms_sensemaking.models.sensemaking import FindingType


@dataclass
class SymbolCodeUpdate(FindingBase):
    """Represents a symbol code update"""

    FINDING_TYPE: FindingType = field(init=False, default=FindingType.MIL_SYMBOL_UPDATE)
    old_symbol_id_code: str
    new_symbol_id_code: str
    acm: Dict
    id_type: str

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

    def get_acm(self) -> Dict:
        return self.acm


class MilSymAttrsPublisher:
    def __init__(
        self,
        oms_crud_tool: OmsCrudTool,
        version: str,
    ) -> None:
        self.oms_crud_tool = oms_crud_tool
        self.version = version

    def publish_mil_sym_attrs(
        self,
        oms_node: NodeNode,
        symbol_code_updates: List[SymbolCodeUpdate],
        source_id: uuid.UUID,
    ) -> list[
        CreateMilSymAttributesMilSymAttr1 | CreateMilSymAttributesMilSymAttr2 | CreateMilSymAttributesMilSymAttr3
    ]:
        inputs: list[CreateAttributeInput] = self.create_attribute_inputs(
            self.version, oms_node, symbol_code_updates, source_id
        )
        attributes: CreateMilSymAttributes = self.oms_crud_tool.oms_client.create_mil_sym_attributes(
            inputs[0], inputs[1], inputs[2]
        )
        return [attributes.milSymAttr1, attributes.milSymAttr2, attributes.milSymAttr3]

    def create_attribute_inputs(
        self, version: str, oms_node: NodeNode, symbol_code_updates: list[SymbolCodeUpdate], source_id: uuid.UUID
    ) -> list[CreateAttributeInput]:
        attribute_inputs: list[CreateAttributeInput] = []
        for symbol_code_update in symbol_code_updates:
            attribute_input: CreateAttributeInput = CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[
                    SETTINGS.sm_inferenced_label,
                    SETTINGS.mil_sym_sm_label,
                    version,
                    symbol_code_update.id_type,
                ],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol_code_update.new_symbol_id_code,
                confidence=Confidence.UNKNOWN,
                acm=symbol_code_update.get_acm(),
                nodeId=oms_node.id,
                sourceId=source_id,
            )
            attribute_inputs.append(attribute_input)
        return attribute_inputs

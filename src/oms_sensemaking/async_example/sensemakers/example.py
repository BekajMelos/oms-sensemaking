from typing import Any

from oms_sdk.generated.generated_graphql_client import AttributeAttribute, AttributeType, CreateAttributeInput

from oms_sensemaking.core.async_atoms_crud import AsyncAtomsCrudTool
from oms_sensemaking.core.sensemakers import AsyncSensemaker


class ExampleAsyncSensemaker(AsyncSensemaker):
    def __init__(self):
        self.async_oms_crud_tool = AsyncAtomsCrudTool()

    async def process_data(self, attr: AttributeAttribute, config: Any):
        if attr.attributeIri == "Name":
            attribute = CreateAttributeInput(
                attributeIri="HasName",
                attributeValue="true",
                attributeType=AttributeType.BOOLEAN,
                confidence=attr.confidence,
                sourceId=attr.sourceId,
                nodeId=attr.nodeId,
                acm=attr.acm,
                tags=[],
                labels=[],
            )

            response = self.async_oms_crud_tool.create_attribute(attribute)

            return await response
        return None

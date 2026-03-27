from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import NodeNode, ObjectTier

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.mil_symbol.mil_symbol_publisher import MilSymAttrsPublisher, SymbolCodeUpdate


@pytest.fixture
def mock_oms_crud_tool():
    oms_crud_tool = OmsCrudTool()
    oms_crud_tool.oms_client = mock.MagicMock()
    return oms_crud_tool


@pytest.fixture
def oms_node() -> NodeNode:
    node = NodeNode.model_construct(
        id=uuid4(),
        classIri="https://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
        name="test",
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
        symbolIdCode=None,
        tier=ObjectTier.PRIMARY,
        labels=[],
    )

    return node


def test_mil_sym_attr_publisher_init(mock_oms_crud_tool, oms_node):
    mock_source = mock.MagicMock()
    mock_source.id = uuid4()

    publisher = MilSymAttrsPublisher(mock_oms_crud_tool, "1.0.0")
    assert isinstance(publisher.oms_crud_tool, OmsCrudTool)
    assert publisher.version == "1.0.0"


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_mil_sym_attr_publisher_create_attr_inputs(mock_get_acm, mock_oms_crud_tool, oms_node):
    mock_get_acm.return_value = DEFAULT_ACM

    symcodeupdate1 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate2 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate3 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate1.id_type = "D"
    symcodeupdate2.id_type = "C"
    symcodeupdate3.id_type = "B"
    symcodeupdate1.new_symbol_id_code = "new D"
    symcodeupdate2.new_symbol_id_code = "new C"
    symcodeupdate3.new_symbol_id_code = "new B"
    mock_symbol_code_updates = [symcodeupdate1, symcodeupdate2, symcodeupdate3]

    mock_source = mock.MagicMock()
    mock_source.id = uuid4()

    publisher = MilSymAttrsPublisher(mock_oms_crud_tool, "1.0.0")
    res = publisher.create_attribute_inputs("1.0.0", oms_node, mock_symbol_code_updates, mock_source.id)
    assert len(res) == 3
    assert res[0].attributeValue == "new D"
    assert res[1].attributeValue == "new C"
    assert res[2].attributeValue == "new B"


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_mil_sym_attr_publisher_publish(mock_get_acm, mock_oms_crud_tool, oms_node):
    mock_get_acm.return_value = DEFAULT_ACM

    symcodeupdate1 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate2 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate3 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate1.id_type = "D"
    symcodeupdate2.id_type = "C"
    symcodeupdate3.id_type = "B"
    symcodeupdate1.new_symbol_id_code = "new D"
    symcodeupdate2.new_symbol_id_code = "new C"
    symcodeupdate3.new_symbol_id_code = "new B"
    mock_symbol_code_updates = [symcodeupdate1, symcodeupdate2, symcodeupdate3]

    mock_source = mock.MagicMock()
    mock_source.id = uuid4()

    publisher = MilSymAttrsPublisher(mock_oms_crud_tool, "1.0.0")
    res = publisher.create_attribute_inputs("1.0.0", oms_node, mock_symbol_code_updates, mock_source.id)
    attrs = publisher.publish_mil_sym_attrs(oms_node, mock_symbol_code_updates, mock_source.id)

    mock_oms_crud_tool.oms_client.create_mil_sym_attributes.assert_called_once_with(res[0], res[1], res[2])
    assert len(attrs) == 3

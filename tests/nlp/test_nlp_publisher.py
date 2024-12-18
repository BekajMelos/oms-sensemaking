from typing import Iterator
from unittest import mock

import pytest
from oms_sdk import DEFAULT_ACM
from sqlalchemy.orm import Session

from oms_sensemaking.nlp.nlp_oms_publisher import NlpOmsPublisher
from tests.nlp.mock_findings import empty_findings, large_findings


@pytest.fixture
def mock_db(db: Session) -> Iterator[Session]:
    yield db


@pytest.fixture
def nlp_publisher(mock_source, mock_oms_crud_tool):
    publisher = NlpOmsPublisher(
        source_id=mock_source.id, acm=DEFAULT_ACM, oms_crud_tool=mock_oms_crud_tool)
    yield publisher


def test_publish(mock_db, nlp_publisher):
    # Run the publishing pipeline
    nlp_publisher.publish(data="", results=large_findings)
    assert nlp_publisher.oms_crud_tool.oms_client.create_node.call_count == 24
    assert nlp_publisher.oms_crud_tool.oms_client.create_relationship.call_count == 24
    assert nlp_publisher.oms_crud_tool.oms_client.create_attribute.call_count == 25

    # Empty findings case
    nlp_publisher.oms_crud_tool.oms_client.reset_mock()
    nlp_publisher.publish(data="", results=empty_findings)
    assert nlp_publisher.oms_crud_tool.oms_client.create_node.call_count == 0
    assert nlp_publisher.oms_crud_tool.oms_client.create_relationship.call_count == 0
    assert nlp_publisher.oms_crud_tool.oms_client.create_attribute.call_count == 0


def test_format_nodes(nlp_publisher):
    assert not nlp_publisher.format_nodes(data="", results=empty_findings)
    assert nlp_publisher.format_nodes(data="", results=large_findings)


def test_format_and_publish_nodes(nlp_publisher):
    # Empty findings case
    empty_published_nodes = nlp_publisher.publish_nodes(nlp_publisher.format_nodes(data="", results=empty_findings))
    assert not empty_published_nodes

    # Regular findings case
    published_nodes = nlp_publisher.publish_nodes(nlp_publisher.format_nodes(data="", results=large_findings))
    assert published_nodes


def test_format_relationships(nlp_publisher):
    assert not nlp_publisher.format_relationships(data="", results=empty_findings)
    assert not nlp_publisher.format_relationships(data="", results=large_findings)

    # Publish some nodes first
    nlp_publisher.publish_nodes(nlp_publisher.format_nodes(data="", results=large_findings))

    assert nlp_publisher.format_relationships(data="", results=large_findings)


def test_format_and_publish_relationships(nlp_publisher):
    # Case when nodes have not been created before relationships for some reason
    assert not nlp_publisher.publish_relationships(nlp_publisher.format_relationships(data="", results=large_findings))

    # Publish some nodes for the relationships to be based on
    nlp_publisher.publish_nodes(nlp_publisher.format_nodes(data="", results=large_findings))

    # Publish the relationships
    empty_published_relationships = nlp_publisher.publish_relationships(
        nlp_publisher.format_relationships(data="", results=empty_findings)
    )
    assert not empty_published_relationships

    published_relationships = nlp_publisher.publish_relationships(
        nlp_publisher.format_relationships(data="", results=large_findings)
    )
    assert published_relationships


def test_format_and_publish_attributes(nlp_publisher):
    # Test case where nodes have not been created beforehand
    assert not nlp_publisher.publish_attributes(nlp_publisher.format_attributes(data="", results=large_findings))
    assert nlp_publisher.oms_crud_tool.oms_client.create_attribute.call_count == 0

    # Test case when nodes have been created
    nlp_publisher.publish_nodes(nlp_publisher.format_nodes(data="", results=large_findings))
    formatted_attributes = nlp_publisher.format_attributes(data="", results=large_findings)
    for attr in formatted_attributes:
        assert attr.sourceId == nlp_publisher.source_id

    nlp_publisher.publish_attributes(formatted_attributes)
    nlp_publisher.oms_crud_tool.oms_client.create_attribute.assert_has_calls(
        [mock.call(attr) for attr in formatted_attributes], any_order=True)

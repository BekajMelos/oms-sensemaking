from typing import Iterator

import pytest
from oms_sdk import DEFAULT_ACM
from sqlalchemy.orm import Session

from oms_sensemaking.nlp.nlp_publisher import NlpOmsPublisher
from tests.nlp.mock_findings import empty_findings, large_findings


@pytest.fixture
def mock_db(db: Session) -> Iterator[Session]:
    yield db


@pytest.fixture
def nlp_publisher(mock_source):
    publisher = NlpOmsPublisher(source_id=mock_source.id, acm=DEFAULT_ACM)
    yield publisher


def test_publish(mock_db, nlp_publisher):
    # Run the publishing pipeline
    nodes, relationships = nlp_publisher.publish(large_findings)
    assert nodes
    assert relationships

    # Empty findings case
    nodes, relationships = nlp_publisher.publish(empty_findings)
    assert not nodes
    assert not relationships


def test_format_and_publish_nodes(nlp_publisher):
    # Empty findings case
    empty_published_nodes = nlp_publisher.format_and_publish_nodes(empty_findings)
    assert not empty_published_nodes

    # Regular findings case
    published_nodes = nlp_publisher.format_and_publish_nodes(large_findings)
    assert published_nodes


def test_format_and_publish_relationships(nlp_publisher):
    # Case when nodes have not been created before relationships for some reason
    published_relationships = nlp_publisher.format_and_publish_relationships(large_findings)
    assert not published_relationships

    # Publish some nodes for the relationships to be based on
    nlp_publisher.format_and_publish_nodes(large_findings)

    # Publish the relationships
    empty_published_relationships = nlp_publisher.format_and_publish_relationships(empty_findings)
    assert not empty_published_relationships

    published_relationships = nlp_publisher.format_and_publish_relationships(large_findings)
    assert published_relationships


def test_format_and_publish_attribute(nlp_publisher):
    entity_value = large_findings["ner_entities"][0]["value"]
    entity_id = large_findings["ner_entities"][0]["uuid"]

    # Test case where nodes have not been created beforehand
    assert not nlp_publisher.format_and_publish_attribute(
        entity_value=entity_value,
        entity_id=entity_id,
        published_node_id="test_node_id",
    )

    # Test case when nodes have been created
    published_nodes = nlp_publisher.format_and_publish_nodes(large_findings)
    published_attribute = nlp_publisher.format_and_publish_attribute(
        entity_value=entity_value,
        entity_id=entity_id,
        published_node_id=published_nodes[0].id,
    )
    assert published_attribute
    assert published_attribute.source.id == nlp_publisher.source_id
    assert published_attribute.attributeValue == entity_value

from typing import Iterator

import pytest
from sqlalchemy.orm import Session

from oms_sensemaking.nlp.nlp_publisher import NlpOmsPublisher
from tests.nlp.mock_findings import empty_findings, large_findings


@pytest.fixture
def mock_db(db: Session) -> Iterator[Session]:
    yield db


@pytest.fixture
def nlp_publisher(mock_source):
    publisher = NlpOmsPublisher(source_id=mock_source.id)
    yield publisher


def test_publish(mock_db, nlp_publisher):
    # Run the publishing pipeline
    nodes, relationships = nlp_publisher.publish(large_findings)
    assert nodes
    assert relationships


def test_format_and_publish_nodes(nlp_publisher):
    # Publish the nodes
    empty_published_nodes = nlp_publisher.format_and_publish_nodes(empty_findings)
    published_nodes = nlp_publisher.format_and_publish_nodes(large_findings)

    assert not empty_published_nodes
    assert published_nodes


def test_format_and_publish_relationships(nlp_publisher):
    # Case when nodes have not been created before relationships for some reason
    published_relationships = nlp_publisher.format_and_publish_relationships(large_findings)
    assert not published_relationships

    # Publish some nodes for the relationships to be based on
    nlp_publisher.format_and_publish_nodes(large_findings)

    # Publish the relationships
    empty_published_relationships = nlp_publisher.format_and_publish_relationships(empty_findings)
    published_relationships = nlp_publisher.format_and_publish_relationships(large_findings)

    assert not empty_published_relationships
    assert published_relationships


def test_format_and_publish_attribute(nlp_publisher):
    # Test case where nodes have not been created beforehand
    assert not nlp_publisher.format_and_publish_attribute(
        entity_value=large_findings["ner_entities"][0]["value"],
        entity_id=large_findings["ner_entities"][0]["uuid"],
        published_node_id="test_node_id",
    )

    # Test case when nodes have been created
    published_nodes = nlp_publisher.format_and_publish_nodes(large_findings)
    assert nlp_publisher.format_and_publish_attribute(
        entity_value=large_findings["ner_entities"][0]["value"],
        entity_id=large_findings["ner_entities"][0]["uuid"],
        published_node_id=published_nodes[0].id,
    )

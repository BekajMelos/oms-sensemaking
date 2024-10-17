from typing import Iterator

import pytest
from sqlalchemy.orm import Session

from oms_sensemaking.nlp.nlp_publisher import NlpOmsPublisher

publisher = NlpOmsPublisher(source_id="test_source")


@pytest.fixture
def mock_db(db: Session) -> Iterator[Session]:
    yield db


def test_publisher_pipeline(mock_db):
    pytest.skip("Skipping because this function is not implemented yet.")


def test_format_nodes():
    pytest.skip("Skipping because this function is not implemented yet.")


def test_format_relationships():
    pytest.skip("Skipping because this function is not implemented yet.")


def test_format_attributes():
    pytest.skip("Skipping because this function is not implemented yet.")


def test_publish_nodes(mock_db):
    pytest.skip("Skipping because this function is not implemented yet.")


def test_publish_relationships(mock_db):
    pytest.skip("Skipping because this function is not implemented yet.")


def test_publish_attributes(mock_db):
    pytest.skip("Skipping because this function is not implemented yet.")

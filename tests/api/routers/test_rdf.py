from unittest.mock import patch

import pytest
from fastapi import HTTPException, Response

from oms_sensemaking.api.routers.rdf import rdf_resolver
from oms_sensemaking.api.schemas.rdf_format import RDFFormat


def test_rdf_resolver_success():
    obj_id = "12345"
    rdf_data = "<rdf>data</rdf>"

    with (
        patch("oms_sensemaking.api.routers.rdf.require_user_dn", return_value="test"),
        patch("oms_sensemaking.api.routers.rdf.OmsCrudTool") as mock_crud,
        patch("oms_sensemaking.api.routers.rdf.RDFClient") as mock_client,
    ):
        # Mock the RDF client return value
        mock_client.return_value.get_rdf_from_id.return_value = rdf_data

        response: Response = rdf_resolver(user_dn="test", obj_id=obj_id, format=RDFFormat.turtle)

        mock_crud.assert_called_once()

        assert response.status_code == 200
        assert response.media_type == "text/plain"
        assert response.body.decode() == rdf_data

        # Ensure the RDF client was used correctly
        mock_client.return_value.get_rdf_from_id.assert_called_once()


def test_rdf_resolver_not_found():
    obj_id = "invalid"

    with (
        patch("oms_sensemaking.api.routers.rdf.require_user_dn", return_value="test"),
        patch("oms_sensemaking.api.routers.rdf.OmsCrudTool"),
        patch("oms_sensemaking.api.routers.rdf.RDFClient") as mock_client,
    ):
        # Simulate "object not found"
        mock_client.return_value.get_rdf_from_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            rdf_resolver(user_dn="test", obj_id=obj_id, format=RDFFormat.jsonld)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Object not found"

from unittest import mock

from oms_sensemaking.core.port_ingest import import_aggressor_port_data


@mock.patch("oms_sensemaking.in_port.port_ingest.check_ports", return_value=False)
@mock.patch("oms_sensemaking.in_port.port_ingest.json.load")
@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("oms_sensemaking.in_port.port_ingest.db_session")
def test_import_geodata_success(mock_db_session, mock_json_load):

    mock_json_load.return_value = [
        {
            "id": "observation-25",
            "capco": "U",
            "tags": "AGGRESSOR;WORLD-PORT-INDEX",
            "labels": "",
            "classIri": "http://www.ontologyrepository.com/CommonCoreOntologies/ObjectTrackPoint",
            "displayValue": "The port's location.",
            "confidence": "HIGH",
            "sourceId": "WPI-source-0",
            "nodeId": "node-62400.0",
            "geometry": '{"type": "Feature", "geometry": {"type": "Point", "coordinates": [129.883333, 33.283333]}}',
            "startTime": "2026-03-30T14:33:11Z",
            "endTime": "2026-03-30T14:33:11Z",
        }
    ]

    result = import_aggressor_port_data()

    assert result is True
    mock_db_session.return_value.__enter__.return_value.add.assert_called_once()
    assert mock_db_session.return_value.__enter__.return_value.commit.called()


@mock.patch("oms_sensemaking.core.cocom.check_geodata", return_value=False)
@mock.patch("oms_sensemaking.core.cocom.json.load")
@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("oms_sensemaking.core.cocom.db_session")
def test_import_geodata_error(mock_db_session, mock_json_load):

    mock_json_load.return_value = [{"id": "MALFORMED"}]

    result = import_aggressor_port_data()

    assert result is False
    mock_db_session.return_value.__enter__.return_value.add.assert_not_called()
    mock_db_session.return_value.__enter__.return_value.rollback.assert_called()

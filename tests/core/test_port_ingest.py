# import xml.etree.ElementTree as ET
# from unittest import mock

# from oms_sensemaking.core.port_ingest import import_geo_data, import_kml_data
# from oms_sensemaking.models.port_ingest import CocomArea, CocomType


# @mock.patch("oms_sensemaking.core.cocom.check_geodata", return_value=False)
# @mock.patch("oms_sensemaking.core.cocom.json.load")
# @mock.patch("builtins.open", new_callable=mock.mock_open)
# @mock.patch("oms_sensemaking.core.cocom.db_session")
# def test_import_geodata_success(mock_db_session, mock_file, mock_json_load, mock_check_geodata):

#     mock_json_load.return_value = {
#         "features": [
#             {
#                 "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
#                 "properties": {"oth_fcs": "U.S. Africa Command"},
#             }
#         ]
#     }

#     result = import_geo_data()

#     assert result is True
#     mock_db_session.return_value.__enter__.return_value.add.assert_called_once()
#     # Verify the object added to the session has the correct Enum value
#     added_obj = mock_db_session.return_value.__enter__.return_value.add.call_args[0][0]
#     assert isinstance(added_obj, CocomArea)
#     assert added_obj.cocom_type == CocomType.AFRICOM
#     assert mock_db_session.return_value.__enter__.return_value.commit.called


# @mock.patch("oms_sensemaking.core.cocom.check_geodata", return_value=False)
# @mock.patch("oms_sensemaking.core.cocom.json.load")
# @mock.patch("builtins.open", new_callable=mock.mock_open)
# @mock.patch("oms_sensemaking.core.cocom.db_session")
# def test_import_geodata_error(mock_db_session, mock_file, mock_json_load, mock_check_geodata):

#     mock_json_load.return_value = {"features": ["bad_json"]}

#     result = import_geo_data()

#     assert result is False
#     mock_db_session.return_value.__enter__.return_value.add.assert_not_called()
#     mock_db_session.return_value.__enter__.return_value.rollback.assert_called()


# @mock.patch("oms_sensemaking.core.cocom.check_geodata", return_value=False)
# @mock.patch("oms_sensemaking.core.cocom.ET.parse")
# @mock.patch("oms_sensemaking.core.cocom.db_session")
# def test_import_kml_data_success(mock_db_session, mock_et_parse, mock_check_geodata):

#     kml_content = """<kml><Placemark>
#         <SimpleData name="oth_fcs">U.S. European Command</SimpleData>
#         <Polygon><coordinates>10,20 10,21 11,21 10,20</coordinates></Polygon>
#     </Placemark></kml>"""
#     fake_root = ET.fromstring(kml_content)

#     # Configure the mock tree to return our fake root
#     mock_tree = mock.MagicMock()
#     mock_tree.getroot.return_value = fake_root
#     mock_et_parse.return_value = mock_tree

#     result = import_kml_data()

#     assert result is True
#     mock_db_session.return_value.__enter__.return_value.add.assert_called_once()

#     added_obj = mock_db_session.return_value.__enter__.return_value.add.call_args[0][0]

#     assert added_obj.cocom_type == CocomType.EUCOM
#     mock_db_session.return_value.__enter__.return_value.commit.assert_called_once()


# @mock.patch("oms_sensemaking.core.cocom.check_geodata", return_value=False)
# @mock.patch("oms_sensemaking.core.cocom.ET.parse")
# @mock.patch("oms_sensemaking.core.cocom.db_session")
# def test_import_kml_data_error(mock_db_session, mock_et_parse, mock_check_geodata):

#     mock_et_parse.side_effect = Exception("Malformed XML or File not found")

#     result = import_kml_data()

#     assert result is False
#     mock_db_session.return_value.__enter__.return_value.rollback.assert_called()

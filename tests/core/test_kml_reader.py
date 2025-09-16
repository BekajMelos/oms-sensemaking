import zipfile
from unittest.mock import MagicMock, patch

import pytest

from oms_sensemaking.core.kml_reader import KMLReader


@pytest.fixture
def reader():
    return KMLReader()


@patch("oms_sensemaking.core.kml_reader.find_all")
@patch("oms_sensemaking.core.kml_reader.mapping")
def test_extract_placemarks_valid(mapping_mock, find_all_mock, reader):
    mock_geom = MagicMock()
    mock_geom.geom_type = "Polygon"
    mapping_mock.return_value = {"type": "Polygon", "coordinates": []}

    mock_pm = MagicMock()
    mock_pm.geometry = mock_geom
    mock_pm.name = "Test"
    mock_pm.description = "Desc"
    find_all_mock.return_value = [mock_pm]

    result = reader.extract_placemarks("dummy_kml_obj")

    assert len(result) == 1
    assert result[0]["properties"]["name"] == "Test"
    mapping_mock.assert_called_once_with(mock_geom)


@patch("oms_sensemaking.core.kml_reader.find_all", return_value=[])
def test_extract_placemarks_no_placemarks(find_all_mock, reader):
    result = reader.extract_placemarks("dummy")
    assert result == []


@patch("oms_sensemaking.core.kml_reader.find_all")
def test_extract_placemarks_invalid_geometry(find_all_mock, reader):
    mock_pm = MagicMock()
    mock_pm.geometry = None
    find_all_mock.return_value = [mock_pm]

    result = reader.extract_placemarks("dummy")
    assert result == []


@patch("oms_sensemaking.core.kml_reader.find_all")
def test_extract_placemarks_non_polygon_geometry(find_all_mock, reader):
    mock_geom = MagicMock()
    mock_geom.geom_type = "LineString"
    mock_pm = MagicMock(geometry=mock_geom)
    find_all_mock.return_value = [mock_pm]

    result = reader.extract_placemarks("dummy")
    assert result == []


@patch("oms_sensemaking.core.kml_reader.find_all")
@patch("oms_sensemaking.core.kml_reader.mapping", side_effect=AttributeError("bad geom"))
@patch("oms_sensemaking.core.kml_reader.LOGGER")
def test_extract_placemarks_mapping_attribute_error(logger_mock, mapping_mock, find_all_mock, reader):
    mock_geom = MagicMock()
    mock_geom.geom_type = "Polygon"
    mock_pm = MagicMock(geometry=mock_geom)
    find_all_mock.return_value = [mock_pm]

    result = reader.extract_placemarks("dummy")
    assert result == []
    logger_mock.warning.assert_called_once()


@patch("oms_sensemaking.core.kml_reader.kml.KML.parse")
@patch.object(KMLReader, "extract_placemarks", return_value=["fake_feature"])
def test_parse_kml_file_success(extract_mock, parse_mock, reader):
    result = reader.parse_kml_file("file.kml")
    parse_mock.assert_called_once_with("file.kml")
    assert result == ["fake_feature"]


@patch("oms_sensemaking.core.kml_reader.kml.KML.parse", side_effect=ValueError("bad file"))
@patch("oms_sensemaking.core.kml_reader.LOGGER")
def test_parse_kml_file_value_error(logger_mock, parse_mock, reader):
    result = reader.parse_kml_file("file.kml")
    assert result == []
    logger_mock.error.assert_called_once()


@patch("oms_sensemaking.core.kml_reader.kml.KML.parse")
@patch("oms_sensemaking.core.kml_reader.zipfile.ZipFile")
@patch.object(KMLReader, "extract_placemarks", return_value=["fake_feature"])
def test_parse_kmz_file_success(extract_mock, zipfile_mock, parse_mock, reader):
    mock_zf = MagicMock()
    mock_zf.__enter__.return_value = mock_zf
    mock_zf.namelist.return_value = ["doc.kml"]
    mock_zf.open.return_value.__enter__.return_value = "file_obj"
    zipfile_mock.return_value = mock_zf

    result = reader.parse_kmz_file("file.kmz")

    zipfile_mock.assert_called_once_with("file.kmz", "r")
    parse_mock.assert_called_once_with("file_obj")
    assert result == ["fake_feature"]


@patch("oms_sensemaking.core.kml_reader.zipfile.ZipFile")
@patch("oms_sensemaking.core.kml_reader.LOGGER")
def test_parse_kmz_file_no_kml(logger_mock, zipfile_mock, reader):
    mock_zf = MagicMock()
    mock_zf.__enter__.return_value = mock_zf
    mock_zf.namelist.return_value = ["not_a_kml.txt"]
    zipfile_mock.return_value = mock_zf

    result = reader.parse_kmz_file("file.kmz")
    assert result == []
    logger_mock.error.assert_called_once()


@patch("oms_sensemaking.core.kml_reader.zipfile.ZipFile", side_effect=zipfile.BadZipFile("bad zip"))
@patch("oms_sensemaking.core.kml_reader.LOGGER")
def test_parse_kmz_file_bad_zip(logger_mock, zipfile_mock, reader):
    result = reader.parse_kmz_file("file.kmz")
    assert result == []
    logger_mock.error.assert_called_once()

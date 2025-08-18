from unittest.mock import MagicMock, patch

from oms_sensemaking.iw.sensemakers.process_observables import process_observables


class DummyObservable:
    """dummy observable for unsupported type testing"""

    def __init__(self, **kwargs):
        pass

    def initialize(self, id, client):
        return self

    def update_data(self):
        pass


def test_get_nodes_exception_handling(caplog):
    """test error handling when get_nodes raises exception"""
    import oms_sensemaking.iw.sensemakers.process_observables as proc_obs_mod

    proc_obs_mod.LOGGER.setLevel("ERROR")
    with patch("oms_sensemaking.iw.sensemakers.process_observables.oms_crud_tool") as mock_oms_client:
        mock_oms_client.get_nodes.side_effect = Exception("Database connection failed")

        with caplog.at_level("ERROR", logger=proc_obs_mod.LOGGER.name):
            process_observables()

        assert "Failed to fetch observables" in caplog.text
        assert "Database connection failed" in caplog.text


def test_no_observables_found(caplog):
    import oms_sensemaking.iw.sensemakers.process_observables as proc_obs_mod

    proc_obs_mod.LOGGER.setLevel("INFO")
    with patch("oms_sensemaking.iw.sensemakers.process_observables.oms_crud_tool") as mock_oms_client:
        mock_oms_client.get_nodes.return_value.data = []

        with caplog.at_level("INFO", logger=proc_obs_mod.LOGGER.name):
            process_observables()
        assert "No observables found" in caplog.text


def test_observable_missing_config(caplog):
    """test when observable has no config attribute"""
    with patch("oms_sensemaking.iw.sensemakers.process_observables.oms_crud_tool") as mock_oms_client:
        observable_node = MagicMock()
        observable_node.id = "obs1"
        mock_oms_client.get_nodes.return_value.data = [observable_node]
        mock_oms_client.get_attributes.return_value.data = []

        process_observables()
        assert "No config found for observable obs1" in caplog.text


def test_observable_unsupported_type(caplog):
    """test when observable has unsupported queryType"""
    with (
        patch("oms_sensemaking.iw.sensemakers.process_observables.oms_crud_tool") as mock_oms_client,
        patch("oms_sensemaking.iw.sensemakers.process_observables.QUERY_CLASS_MAP", {"dummy": DummyObservable}),
    ):
        observable_node = MagicMock()
        observable_node.id = "obs2"
        mock_oms_client.get_nodes.return_value.data = [observable_node]
        config_attr = MagicMock()
        config_attr.attributeValue = '{"queryType": "not_supported"}'
        mock_oms_client.get_attributes.return_value.data = [config_attr]

        process_observables()
        assert "Unsupported query type for observable obs2: not_supported" in caplog.text


def test_observable_supported_type_calls_update_data():
    """test when observable has supported queryType and update_data is called"""
    import oms_sensemaking.iw.sensemakers.process_observables as proc_obs_mod

    with (
        patch("oms_sensemaking.iw.sensemakers.process_observables.oms_crud_tool") as mock_oms_client,
        patch("oms_sensemaking.iw.sensemakers.process_observables.GeofenceObservable") as mock_geofence_class,
    ):
        observable_node = MagicMock()
        observable_node.id = "obs3"
        mock_oms_client.get_nodes.return_value.data = [observable_node]
        config_attr = MagicMock()
        config_attr.attributeValue = (
            '{"queryType": "geofence", "location": {"type": "Polygon", "coordinates": '
            + '[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}, "fullyObservedCount": 1, "timeBounds": {"sinceLastQuery": false, '
            + '"startTime": "2024-01-01T00:00:00Z", "endTime": "2024-01-01T01:00:00Z"}}'
        )
        mock_oms_client.get_attributes.return_value.data = [config_attr]

        mock_geofence_instance = MagicMock()
        mock_geofence_instance.initialize = MagicMock(return_value=mock_geofence_instance)
        mock_geofence_instance.update_data = MagicMock()
        mock_geofence_class.return_value = mock_geofence_instance

        # Patch QUERY_CLASS_MAP in the module so it uses our mock
        proc_obs_mod.QUERY_CLASS_MAP["geofence"] = mock_geofence_class

        process_observables()
        mock_geofence_instance.initialize.assert_called_once_with("obs3", mock_oms_client)
        mock_geofence_instance.update_data.assert_called_once()


def test_observable_exception_handling(caplog):
    """test error handling when observable processing raises exception"""
    import oms_sensemaking.iw.sensemakers.process_observables as proc_obs_mod

    proc_obs_mod.LOGGER.setLevel("ERROR")
    with patch("oms_sensemaking.iw.sensemakers.process_observables.oms_crud_tool") as mock_oms_client:
        observable_node = MagicMock()
        observable_node.id = "obs4"
        mock_oms_client.get_nodes.return_value.data = [observable_node]
        config_attr = MagicMock()
        config_attr.attributeValue = (
            '{"queryType": "geofence", "location": {"type": "Polygon", "coordinates": '
            + '[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}, "fullyObservedCount": 1, "timeBounds": '
            + '{"sinceLastQuery": false, "startTime": "2024-01-01T00:00:00Z", "endTime": "2024-01-01T01:00:00Z"}}'
        )
        mock_oms_client.get_attributes.return_value.data = [config_attr]

        class RaiseException:
            def __init__(self, *a, **kw):
                raise Exception("bad observable config")

        proc_obs_mod.QUERY_CLASS_MAP["geofence"] = RaiseException

        with caplog.at_level("ERROR", logger=proc_obs_mod.LOGGER.name):
            process_observables()
        assert "Error processing observable obs4: bad observable config" in caplog.text

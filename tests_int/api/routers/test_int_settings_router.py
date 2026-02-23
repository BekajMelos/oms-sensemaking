from unittest import mock

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.models.settings import Setting
from oms_sensemaking.service import app


def _auth_override():
    return "test_user"


def test_patch_settings_creates_row(client, db):
    app.dependency_overrides[check_user_dn_in_whitelist] = _auth_override

    with mock.patch("oms_sensemaking.core.settings.apply_settings_updates"):
        resp = client.patch("/settings", json={"settings": {"rabbitmq_prefetch_count": 123}})
        assert resp.status_code == 204

        row = db.query(Setting).filter_by(field_name="rabbitmq_prefetch_count").first()
        assert row.field_value == 123

    app.dependency_overrides.clear()


def test_patch_settings_updates_existing(client, db):
    app.dependency_overrides[check_user_dn_in_whitelist] = _auth_override

    existing = Setting(field_name="rabbitmq_prefetch_count", field_value=5)
    db.add(existing)
    db.commit()

    with mock.patch("oms_sensemaking.core.settings.apply_settings_updates"):
        resp = client.patch("/settings", json={"settings": {"rabbitmq_prefetch_count": 250}})
        assert resp.status_code == 204

        db.refresh(existing)
        assert existing.field_value == 250

    app.dependency_overrides.clear()


def test_patch_settings_multiple(client, db):
    app.dependency_overrides[check_user_dn_in_whitelist] = _auth_override

    payload = {
        "settings": {
            "rabbitmq_prefetch_count": 100,
            "maximum_oms_api_calls": 50000,
        }
    }

    with mock.patch("oms_sensemaking.core.settings.apply_settings_updates"):
        resp = client.patch("/settings", json=payload)
        assert resp.status_code == 204

        rows = db.query(Setting).all()
        names = {r.field_name for r in rows}
        assert names == {"rabbitmq_prefetch_count", "maximum_oms_api_calls"}

    app.dependency_overrides.clear()


def test_get_settings_returns_db_state(client, db):
    app.dependency_overrides[check_user_dn_in_whitelist] = _auth_override

    db.add(Setting(field_name="rabbitmq_prefetch_count", field_value=250))
    db.commit()

    resp = client.get("/settings")
    assert resp.status_code == 200

    data = resp.json()
    assert data["rabbitmq_prefetch_count"] == 250

    app.dependency_overrides.clear()


def test_patch_settings_invalid_value(client, db):
    client.app.dependency_overrides[check_user_dn_in_whitelist] = _auth_override

    resp = client.patch("/settings", json={"settings": {"rabbitmq_prefetch_count": -1}})
    assert resp.status_code == 422

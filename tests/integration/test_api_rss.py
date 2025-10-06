from unittest.mock import MagicMock, patch


def test_health_endpoint_returns_ok(client):
    response = client.get("/api/healthz")
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "healthy"


def test_trigger_rss_requires_admin(client):
    response = client.post("/api/jobs/rss")
    assert response.status_code == 401


def _login_admin(client, admin_user):
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["role"] = "admin"
        session["username"] = admin_user.username


@patch("app.blueprints.api.views.RSSService")
def test_trigger_rss_all_sources(mock_service, client, admin_user):
    mock_instance = MagicMock()
    mock_instance.run_all_rss.return_value = {
        "success": True,
        "message": "ok",
        "job_run_id": 1,
        "stats": {"processed": 1},
    }
    mock_service.return_value = mock_instance

    _login_admin(client, admin_user)
    response = client.post("/api/jobs/rss")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["message"] == "ok"
    assert payload["data"]["job_run_id"] == 1
    mock_instance.run_all_rss.assert_called_once()


@patch("app.blueprints.api.views.RSSService")
def test_trigger_single_rss_source(mock_service, client, admin_user):
    mock_instance = MagicMock()
    mock_instance.run_single_rss.return_value = {
        "success": True,
        "message": "ok",
        "job_run_id": 2,
    }
    mock_service.return_value = mock_instance

    _login_admin(client, admin_user)
    response = client.post("/api/jobs/rss", json={"rss_id": 5})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["job_run_id"] == 2
    mock_instance.run_single_rss.assert_called_once_with(5)

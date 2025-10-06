from app.services.stats_service import StatsService


def test_dashboard_stats_contains_core_metrics(app):
    with app.app_context():
        stats = StatsService.get_dashboard_stats()
        assert {"total_news", "total_sources", "total_users"}.issubset(stats)
        assert stats["total_sources"] >= 0


def test_trend_and_distribution_helpers_return_iterables(app):
    with app.app_context():
        trend = StatsService.get_news_trend(days=7)
        dist = StatsService.get_source_distribution()
        assert isinstance(trend, list)
        assert isinstance(dist, list)


def test_admin_stats_routes_require_authentication(client):
    response = client.get("/admin/stats")
    assert response.status_code == 302


def test_admin_stats_routes_accessible_for_admin(client, admin_user):
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["role"] = "admin"

    dashboard = client.get("/admin/stats")

    assert dashboard.status_code == 200


def test_admin_stats_api_refresh_returns_json(client, admin_user):
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["role"] = "admin"

    response = client.get("/admin/api/stats/refresh")
    assert response.status_code == 200
    payload = response.get_json()
    assert "details" in payload

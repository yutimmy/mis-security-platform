# Test Suite Structure

The automated test suite now follows a layered layout:

- `tests/unit/` contains fast, isolated tests that mock external services.
- `tests/integration/` exercises Flask blueprints, database interactions, and service plumbing via shared fixtures.
- `tests/manual/` hosts legacy diagnostic scripts and HTML fixtures that are still useful for manual verification but are no longer executed by pytest.

Shared fixtures live in `tests/conftest.py`; they configure a dedicated SQLite database, seed an admin account, and expose helpers such as `client`, `authenticated_client`, and `admin_user`. Add new tests to the unit or integration folders and reuse these fixtures instead of touching application state directly.

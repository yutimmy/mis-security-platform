# Repository Guidelines

## Project Structure & Module Organization
`app.py` starts the Flask service with settings from `config.Config` and the factory in `app/__init__.py`. Feature blueprints reside in `app/blueprints/` with matching templates and static assets inside `app/templates/` and `app/static/`. Crawler and AI code stays in `crawlers/`, shared helpers in `utils/`, and long-lived artifacts in `data/` (SQLite) plus `instance/` (secret config). Tests, docs, and prompt assets live in `tests/`, `docs/`, and `prompts/`; keep new modules in these directories so imports remain predictable.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: prepare the expected virtual environment.
- `pip install -r requirements.txt`: install Flask, crawler, AI, and pytest dependencies.
- `python init_db.py`: create `data/app.db` with default users, feeds, and tables used by tests.
- `python app.py`: launch the development server at http://127.0.0.1:5000.
- `pytest` or `pytest -k crawler -s`: run the suite or isolate modules while keeping print diagnostics.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, snake_case identifiers, PascalCase classes, and SCREAMING_SNAKE_CASE constants. Register new blueprints through `create_app()` and prefer dependency injection over module-level singletons to avoid circular imports. Add type hints for services, keep comments terse, and mirror the Tailwind utility approach already in the templates when touching UI.

## Testing Guidelines
Pytest with `pytest-flask` is the standard harness; initialize the database first or stub it inside fixtures. Name files `test_<feature>.py`, keep reusable data in helper functions instead of committing generated SQLite files, and run `pytest -s` when crawler or GenAI tests rely on streamed logs. Mock outbound requests and reset app contexts so test runs stay deterministic.

## Commit & Pull Request Guidelines
Write present-tense, imperative commit subjects (`Add admin feed filter`) and keep them under ~72 characters. Limit each commit or PR to a single concern so reviewers can trace crawler, UI, or schema changes cleanly. PRs should explain the change, link issues, document tests, and include screenshots or API samples for user-facing updates; mention new secrets or operational steps explicitly.

## Environment & Security Tips
Copy `.env.example` to `.env`, provide Google GenAI and Discord credentials, and keep secrets out of Git. Rotate the seeded admin password after `init_db.py`, respect Jina Reader or Sploitus rate limits, and ensure generated databases or caches stay ignored before submitting changes.

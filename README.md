# Boat Maintenance & Mooring Service Manager

A clean-room **Django Admin** platform for managing boat moorings, customers, technicians, service orders, and **before/after photo proofs**—rebuilt from scratch with strict environment-based configuration, normalized media models, automated tests, and a `uv`-powered CI pipeline.

## Key Features
- **Django Admin-First Workflow**: Customized `ModelAdmin` views with inline before/after photo proof galleries, search, filters, and safe `format_html` thumbnails.
- **Normalized Domain Models**: `Customer`, `Boat`, `BoatPhoto`, `Employee`, `ServiceOrder`, `ServiceProofPhoto`, `Product`, and `OrderDetail`.
- **Zero-Secret Configuration**: All secrets and runtime flags are loaded from environment variables (see [`.env.example`](.env.example)).
- **AI Harness & CI**: Configured with [`AGENTS.md`](AGENTS.md), `ruff`, `pytest-django`, and GitHub Actions via `uv`.

## Quickstart
```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

## Quality Checks
```bash
uv run ruff check .
uv run pytest -v
uv run python manage.py check
```

# AGENTS.md — AI Coding Harness for Boat Maintenance

## Overview
Django Admin-first application for managing boat moorings, customers, technicians, maintenance service orders, parts/line items, and before/after photo proofs.

## Tech Stack & Tooling
- **Language / Runtime**: Python 3.12+
- **Package Manager**: `uv` (never use bare `pip` in CI or local dev)
- **Framework**: Django 5.x + Pillow
- **Testing & Linting**: `pytest` (`pytest-django`) + `ruff`

## Commands
```bash
uv sync --locked
uv run ruff check .
uv run pytest -v
uv run python manage.py check
```

## Security & Hygiene Rules (Mandatory)
1. **Never commit secrets**: `.env`, service-account JSONs, or hardcoded `SECRET_KEY` values are strictly forbidden. Read all configuration from environment variables (`os.environ`).
2. **Safe HTML rendering**: Always use `django.utils.html.format_html()` / `format_html_join()` for admin image previews. Never pass f-strings into `mark_safe()`.
3. **Upload validation**: Validate image extensions and keep media paths scoped to `boats/<id>/` and `orders/<id>/<stage>/`.

## Git Flow Workflow
- `main`: Production-ready releases only (tagged `vX.Y.Z`).
- `develop`: Integration branch for completed features.
- `feature/<slug>`: Branched from `develop`, tested with `uv run ruff check .` and `uv run pytest -v`, then merged back into `develop` (`--no-ff`).
- `release/<version>`: Branched from `develop` to finalize release prep, then merged into `main` (and tagged) and `develop`.

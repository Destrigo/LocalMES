# Contributing to LocalMES

Thanks for helping. Keep the product local-first, ERP-agnostic, and usable without an IT team.

## Rules

- Code, database columns, and API paths in **English**
- UI copy via i18n (`en` + `it` minimum)
- No vendor-specific connectors in core (ERP adapters belong elsewhere)
- No secrets, real customer data, or machine-specific paths in the repo
- Do not add `Co-authored-by` trailers to commits

## Development

1. Fork / branch from `main`
2. Backend: `app/backend` + pytest when added
3. Frontend: `app/frontend`
4. Open a PR with a short summary and test notes

## API

All domain resources live under `/api/v1`. Schemas should expose every persisted field except secrets (`password_hash`, raw API keys).

# LocalMES — Design Spec

**Date:** 2026-07-29  
**Status:** Draft for review  
**Source inspiration:** private `tmp_mes` (Newcos-specific MES) — **new clean repository**, no shared git history

---

## 1. Product positioning

**LocalMES** is a local-first Manufacturing Execution System for small manufacturers that are starting to digitize production and cannot afford an IT team or a heavyweight ERP/MES suite.

- Download → configure → run on a shop PC / LAN
- No mandatory cloud, no mandatory ERP connector
- Browser UI for operators and back office; **full HTTP API** for any later integration

**Not in scope for branding/history:** Newcos, Danea Easyfatt, internal network shares, machine-specific paths, real customer/production data.

**Name note:** `SimpleMES` already exists ([simplemes/simplemes-core](https://github.com/simplemes/simplemes-core)). We use **LocalMES**.

---

## 2. Goals and non-goals

### Goals (v1)

- Runnable locally (one process in production: FastAPI serves the SPA)
- English codebase; UI in **English + Italian** (i18n-ready for more locales)
- Core shop-floor loop: master data → customer orders / production jobs → line operations → dashboard / signage → reports
- Excel/CSV import via templates (no ERP)
- Folder-based SQLite backup
- Demo seed data for instant tryout
- **Complete REST API covering every persisted entity and every field** (see §5), documented via OpenAPI

### Non-goals (v1)

- ERP connectors (Danea or others)
- Supabase / SaaS backup
- LLM / PDF ingestion
- Native mobile apps (responsive browser is enough)
- Complex guided onboarding wizard (optional v1.1)
- Multi-tenant cloud hosting as primary mode

---

## 3. Repository strategy

| Decision | Choice |
|----------|--------|
| History | **New repo** `LocalMES` — selective copy from `tmp_mes`, then rename/i18n/strip |
| License | MIT (permissive; friendly to SMEs embedding/forking) |
| Language (code) | English (modules, routes, DB columns, commits, technical docs) |
| Language (UI) | i18n: `en`, `it` at minimum |
| Layout | See §4 |

Do **not** publish or rewrite `tmp_mes` history (contains paths, shares, and business data references).

---

## 4. Architecture

### Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend | Python 3.10+, FastAPI | Simple packaging, excellent OpenAPI |
| DB | SQLite (SQLAlchemy) | Single file, easy backup, no DBA |
| Frontend | React + Vite + Tailwind | Existing `tmp_mes` base |
| Auth (UI) | Server-side session cookie | Simple for LAN use |
| Auth (API integrations) | API keys (header) | Machine-to-machine without browser session |
| Deploy | Scripts (Win/sh) + Docker Compose | Non-technical and technical paths |

### Directory layout

```
LocalMES/
  app/
    backend/           # FastAPI, models, routers, alembic
    frontend/          # React SPA
  templates/           # Excel/CSV import samples
  scripts/             # start.bat, start.sh, seed_demo.py
  docker-compose.yml
  docs/
    user/              # Short user guides (en/it)
    superpowers/specs/ # Design docs
  .env.example
  LICENSE
  README.md
  CONTRIBUTING.md
```

### Runtime modes

- **Dev:** `MES_DEV=1` — Vite on :3000, API on :8000, CORS enabled
- **Prod:** `MES_DEV=0` — FastAPI serves `frontend/dist` on :8000 (single URL for the shop)

### What is copied vs dropped from `tmp_mes`

**Keep (then anglicize):** auth, users, master data (lines, groups, cycles/operations), customers, orders, production jobs (ex-commesse), shop-floor operations, dashboard, signage, reports, settings/backup folder, API keys, Excel import flows that are ERP-agnostic.

**Drop:** `sync_danea`, `importa_danea`, `estrai_tutto`, root EFT extractors, `.bat` extraction scripts, real CSV/XLSX/report paths, Fujitsu/Newcos paths, network share defaults, Supabase backup module, Anthropic ingestione (v1), any Newcos-branded docs/assets.

**Schema:** remove `danea_*` columns; if an external reference is useful for imports, use neutral `external_id` (nullable, indexed) on relevant entities.

---

## 5. API-first integration (mandatory)

LocalMES is **API-complete**: anything the UI can read or write, and every field on every domain model, must be available over HTTP so companies can later plug ERP, Excel bots, Power Automate, custom scripts, etc. without forking the UI.

### Principles

1. **Parity:** UI uses the same public API as external clients (no “UI-only” side doors for domain data).
2. **Full field coverage:** request/response schemas expose **all** persisted columns (except secrets: password hashes, raw API key secrets). No silent truncation of fields in list/detail DTOs.
3. **CRUD + actions:** standard REST for resources; explicit action endpoints for domain verbs (e.g. start/pause/complete operation, declare downtime).
4. **OpenAPI:** FastAPI auto-docs at `/docs` in dev; shipped as the integration contract. Schemas must be accurate (Pydantic models, not untyped dicts).
5. **Stable English resource names** in paths and JSON keys (e.g. `/api/v1/work-orders`, `line_group_id`).
6. **Version prefix:** `/api/v1/...` from day one to allow future breaking changes.
7. **Pagination / filtering:** list endpoints support `limit`, `offset` (or cursor), and filters on key foreign keys and statuses.
8. **Idempotency where useful:** create-by-`external_id` upsert or conflict behavior documented for import integrations.

### Customization (no code, no IT)

SMEs configure the MES from **Settings → Custom fields**, not by forking the app:

- **Field definitions** (`/api/v1/field-definitions`): entity, key, label, type (`string|number|boolean|date|select`), required, options, active, sort_order.
- **Values** live in `custom_fields` JSON on: customer, product, work_order, work_order_line, production_order, operation_instance.
- **Add-only schema:** never hard-delete a definition; deactivate instead. `key` / `entity` / `field_type` are immutable after create. Select `options` may only grow.
- Light rules today: required + type coercion + select membership. Enough for plant-specific attributes without a rules engine.

### Auth for integrations

| Client | Mechanism |
|--------|-----------|
| Browser SPA | Session cookie (existing pattern) |
| Scripts / ERP / Zapier-like | API key in `Authorization: Bearer <key>` or `X-API-Key` |

API keys are scoped by role (same permission matrix as users). Key **values** are shown once at creation; only hashes stored.

### Resource map (v1) — every entity gets list/get/create/update/delete unless noted

| Resource | Path (sketch) | Notes |
|----------|---------------|-------|
| Users | `/api/v1/users` | No password hash in responses; `POST` set/reset password as action |
| Auth | `/api/v1/auth/login`, `logout`, `me` | Session |
| API keys | `/api/v1/api-keys` | Superadmin |
| Line groups | `/api/v1/line-groups` | |
| Lines | `/api/v1/lines` | |
| Operation catalog | `/api/v1/operations` | Legend / standard ops |
| Downtime reasons | `/api/v1/downtime-reasons` | |
| Products | `/api/v1/products` | Product codes |
| Cycles | `/api/v1/cycles` | + nested cycle operations |
| Customers | `/api/v1/customers` | |
| Customer orders | `/api/v1/customer-orders` | + lines / components |
| BOMs | `/api/v1/boms` | Optional if kept in schema |
| Work orders / jobs | `/api/v1/work-orders` | Ex-commesse; linked ops |
| Production orders | `/api/v1/production-orders` | If distinct from customer orders in schema |
| Operation instances | `/api/v1/operation-instances` | Live shop-floor state |
| Downtime events | `/api/v1/downtimes` | |
| Settings | `/api/v1/settings` | Key/value; secrets redacted |
| Field definitions | `/api/v1/field-definitions` | Custom fields schema (add-only; deactivate, never delete) |
| Backup logs | `/api/v1/backup-logs` | Read + trigger backup action |
| Dashboard / signage | `/api/v1/dashboard/...` | Read-optimized aggregates |
| Reports | `/api/v1/reports/...` | Export endpoints |
| Import | `/api/v1/imports/...` | Multipart Excel/CSV |

**Shop-floor actions (examples):**  
`POST .../operation-instances/{id}/start|pause|resume|complete`  
`POST .../operation-instances/{id}/downtimes`

Analytics / medallion tables (`EventoRaw`, `Gold*`) if retained: **read-only** API under `/api/v1/analytics/...`, or omitted from v1 public API if only internal—decision: expose read-only if present in DB so integrators can pull KPIs without scraping the UI.

### Error contract

JSON errors: `{ "detail": "...", "code": "optional_machine_code" }` with proper HTTP status. Validation errors list fields. Messages for humans may be localized later; **machine `code` stays English/stable**.

---

## 6. Domain language (English in code)

| Italian (legacy UI) | English (code / API) |
|---------------------|----------------------|
| Commessa | Work order / job |
| Ciclo | Cycle (routing) |
| Linea / Gruppo linea | Line / line group |
| Ordine cliente | Customer order |
| Operativo | Shop floor |
| Fermo | Downtime |
| Distinta base | BOM |

UI copy is translated via i18n files; API and DB stay English.

---

## 7. Internationalization

- Frontend: `react-i18next` (or equivalent) with `locales/en.json`, `locales/it.json`
- Default: browser language, override in Settings
- Import templates: stable English column keys; optional localized header row documented in user guide
- User-facing docs: short guides in `en` and `it`

---

## 8. Onboarding (non-technical path)

1. Install Docker **or** Python 3.10+ and Node 18+
2. Run `scripts/start` (platform script) or `docker compose up`
3. Open `http://localhost:8000`
4. Login `admin` / `admin` → forced password change
5. Optional: load demo seed **or** import Excel templates from `/templates`
6. Create line group → line → cycle → first work order → run on shop floor

Advanced (HTTPS, reverse proxy, env hardening) documented separately, not required for LAN trial.

---

## 9. Configuration

| Variable | Purpose |
|----------|---------|
| `MES_SECRET_KEY` | Session signing (required in prod) |
| `MES_DEV` | `1` dev / `0` prod SPA serving |
| `MES_DATABASE_URL` | Optional; default SQLite file path |
| `MES_BACKUP_DIR` | Default backup folder (overridable in settings) |
| `MES_CORS_ORIGINS` | Extra CORS origins if needed |

No hardcoded hostnames, UNC paths, or vendor install paths in source. `.env.example` only.

---

## 10. Security (v1 baseline)

- bcrypt passwords; forced change on default admin
- API keys hashed at rest
- Secrets never in git (`.gitignore`: `.env`, `*.db`, uploads, backups)
- `/docs` enabled in dev; configurable in prod (default off or behind auth)
- LAN trust model: no HTTPS required for v1 local deploy; document HTTPS for exposed networks

---

## 11. Testing and quality

- Backend: pytest on API CRUD for each resource (at least happy path + auth denial)
- OpenAPI schema snapshot or contractual check that models include all columns
- Frontend: smoke build; critical flows optional later
- CI on the new repo: lint + typecheck + tests

---

## 12. Implementation approach (high level)

1. Scaffold new `LocalMES` repo (LICENSE, README, structure)
2. Port backend models with English names; strip vendor fields
3. Implement `/api/v1` routers with full field schemas + API key auth
4. Port frontend; wire i18n; point to versioned API
5. Templates, seed, start scripts, Docker Compose
6. User docs en/it; CONTRIBUTING
7. Soft-launch checklist: grep for Danea/Newcos/Fujitsu/`192.168`/UNC paths

Detailed task breakdown comes in a separate implementation plan after this spec is approved.

---

## 13. Success criteria

- A non-technical user can run LocalMES on a Windows or Linux PC and complete one production job without external services
- An integrator can create/update/read **every** domain field via `/api/v1` using only OpenAPI + an API key
- Repository contains no company-specific or ERP-vendor-specific coupling
- UI available in English and Italian

---

## Open decisions (resolved)

| Topic | Decision |
|-------|----------|
| Repo | New clean repo |
| ERP | None in v1 |
| Name | LocalMES |
| Code language | English |
| UI languages | en + it |
| API | Full coverage of all entities/fields under `/api/v1` |

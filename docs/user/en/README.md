# LocalMES — User guide (English)

## Install

1. Install Python 3.10+ and Node.js 18+
2. Run `scripts/start.bat` (Windows) or `scripts/start.sh` (Linux/macOS)
3. Open http://localhost:3000
4. Login with `admin` / `admin` and change the password

Or with Docker: `docker compose up --build` then open http://localhost:8000

## First setup

1. **Settings** (superadmin): set `backup_dir`, optionally enable scheduled backup
2. Create **line groups** and **lines**
3. Create **catalog operations** via API `/api/v1/operations` (UI for ops can use API docs) or seed demo:
   `python app/backend/scripts/seed_demo.py`
4. Create **customers** and **products**
5. Create a **work order**, add lines, generate **production orders**
6. On **Shop floor**, start / pause / complete operations

## Import

In Settings → Import, upload CSV/Excel for customers, products, BOMs, production orders.
Templates are in `/templates`.

## Reports

Settings → Reports: Excel or PDF export (session cookie required; open while logged in).

## API integration

- Docs (dev): http://localhost:8000/docs
- Create an API key in Settings
- Send header `X-API-Key: mes_...` or `Authorization: Bearer mes_...`

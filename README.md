# LocalMES

Local-first Manufacturing Execution System for small manufacturers digitizing production without an IT team or ERP lock-in.

- Run on a shop PC / LAN
- Full REST API under `/api/v1` (session cookie or API key)
- UI in English and Italian
- SQLite single-file database + folder backup

## Requirements

- Python 3.10+
- Node.js 18+

## Quick start for non-technical users (Windows)

1. Install [Python 3.10+](https://www.python.org/downloads/) and [Node.js 18+](https://nodejs.org/) (once)
2. Double-click `scripts\start-production.bat`
3. Open http://localhost:8000
4. Login `admin` / `admin` and change the password

Optional later in **Settings**: company name, backup folder.

## Quick start (development)

```bash
# Backend
cd app/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Optional demo data
python scripts/seed_demo.py

# Frontend (other terminal)
cd app/frontend
npm install
npm run dev
```

Open http://localhost:3000 — default login `admin` / `admin` (password change required).

API docs (dev): http://localhost:8000/docs

User guides: [English](docs/user/en/README.md) · [Italiano](docs/user/it/README.md)

## Production (single process)

```bash
cd app/frontend && npm install && npm run build
cd ../backend
set MES_DEV=0
set MES_SECRET_KEY=replace-with-long-random-string
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open http://SERVER:8000

## Docker

```bash
docker compose up --build
```

## Configuration

See `.env.example`. Never commit secrets or `database.db`.

## License

MIT

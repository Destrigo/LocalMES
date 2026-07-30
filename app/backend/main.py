"""LocalMES FastAPI entry point."""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import init_db
from routers import (
    api_keys,
    auth,
    boms_reports,
    customers,
    cycles,
    dashboard,
    field_definitions,
    imports,
    master_data,
    order_events,
    production_orders,
    settings,
    shop_floor,
    users,
    work_orders,
)
from routers.settings import start_backup_scheduler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEV_MODE = os.environ.get("MES_DEV", "1") == "1"
API_PREFIX = "/api/v1"

app = FastAPI(
    title="LocalMES",
    description="Local-first Manufacturing Execution System for small manufacturers",
    version="0.1.0",
    docs_url="/docs" if DEV_MODE else None,
    redoc_url=None,
)

SECRET_KEY = os.environ.get(
    "MES_SECRET_KEY", "localmes-dev-secret-change-me-in-production"
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="mes_session",
    https_only=False,
    same_site="lax",
)

if DEV_MODE:
    origins = os.environ.get(
        "MES_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount all domain routers under /api/v1
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(api_keys.router, prefix=API_PREFIX)
app.include_router(master_data.router, prefix=API_PREFIX)
app.include_router(cycles.router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(work_orders.router, prefix=API_PREFIX)
app.include_router(production_orders.router, prefix=API_PREFIX)
app.include_router(shop_floor.router, prefix=API_PREFIX)
app.include_router(shop_floor.downtimes_router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(settings.router, prefix=API_PREFIX)
app.include_router(field_definitions.router, prefix=API_PREFIX)
app.include_router(boms_reports.boms_router, prefix=API_PREFIX)
app.include_router(boms_reports.reports_router, prefix=API_PREFIX)
app.include_router(imports.router, prefix=API_PREFIX)
app.include_router(order_events.router, prefix=API_PREFIX)

FRONTEND_DIST = os.path.join(BASE_DIR, "..", "frontend", "dist")

if not DEV_MODE and os.path.isdir(FRONTEND_DIST):
    assets = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets):
        app.mount("/assets", StaticFiles(directory=assets), name="spa-assets")

    @app.get("/favicon.svg")
    def favicon():
        return FileResponse(os.path.join(FRONTEND_DIST, "favicon.svg"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str, request: Request):
        if full_path.startswith("api/"):
            return {"detail": "Not found"}
        index = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return {"error": "Frontend not built. Run npm run build in app/frontend."}


@app.on_event("startup")
def startup():
    init_db()
    start_backup_scheduler()


@app.get("/health")
def health():
    return {"status": "healthy", "mode": "dev" if DEV_MODE else "prod", "app": "LocalMES"}

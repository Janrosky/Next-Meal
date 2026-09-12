import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError
from starlette.concurrency import run_in_threadpool

from app.api import router
from app.config import Settings
from app.database import Database
from app.domain import BusinessError
from app.realtime import ChangeFeed
from app.security import AttemptLimiter, AuthService
from app.seed import initialize_business
from app.services.business import COSTA_RICA, BusinessService
from app.services.catalog import CatalogService
from app.services.employees import EmployeeService
from app.services.orders import OrderService

logger = logging.getLogger(__name__)


async def daily_backup(database: Database):
    while True:
        target = (
            database.path.parent
            / "backups"
            / ("automatic-" + datetime.now(COSTA_RICA).strftime("%Y-%m-%d") + ".sqlite3")
        )
        try:
            if not target.exists():
                await run_in_threadpool(database.backup, target)
        except Exception:
            logger.exception("No se pudo crear el respaldo automático.")
        await asyncio.sleep(3600)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_environment()
    database = Database(settings.database_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database.initialize()
        initialize_business(database)
        backup_task = asyncio.create_task(daily_backup(database))
        yield
        backup_task.cancel()
        with suppress(asyncio.CancelledError):
            await backup_task
        database.close()

    app = FastAPI(title="SodaLocal", version="0.1.0", lifespan=lifespan)
    app.state.database = database
    app.state.auth = AuthService(database, settings.session_hours)
    app.state.catalog = CatalogService(database)
    app.state.orders = OrderService(database)
    app.state.employees = EmployeeService(database)
    app.state.business = BusinessService(database)
    app.state.feed = ChangeFeed()
    app.state.order_limiter = AttemptLimiter(limit=120, window=300)

    @app.exception_handler(BusinessError)
    async def business_error(_request: Request, error: BusinessError):
        return JSONResponse({"detail": error.message}, status_code=error.status_code)

    @app.exception_handler(OperationalError)
    async def database_error(_request: Request, error: OperationalError):
        logger.error("SQLite no disponible: %s", type(error).__name__)
        return JSONResponse(
            {"detail": "La base de datos está ocupada. Volvé a intentar."}, status_code=503
        )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(router)
    if settings.static_path.is_dir():
        app.mount("/", StaticFiles(directory=settings.static_path, html=True), name="frontend")
    return app


app = create_app()

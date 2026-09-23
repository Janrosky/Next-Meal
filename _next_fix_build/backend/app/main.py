from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app.api import router
from app.config import Settings
from app.database import Database
from app.seed import initialize_demo


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_environment()
    database = Database(settings.database_path)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        database.initialize()
        initialize_demo(database)
        yield
        database.close()

    app = FastAPI(title="Next-Fix", version="0.1.0", lifespan=lifespan)
    app.state.database = database
    app.include_router(router)

    @app.exception_handler(OperationalError)
    async def database_error(_request: Request, _error: OperationalError):
        return JSONResponse({"detail": "La base local está ocupada. Intentá nuevamente."}, 503)

    @app.middleware("http")
    async def secure_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    if settings.static_path.is_dir():
        app.mount("/", StaticFiles(directory=settings.static_path, html=True), name="frontend")
    return app


app = create_app()

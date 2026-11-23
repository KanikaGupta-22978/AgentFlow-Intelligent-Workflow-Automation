
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.execution_routes import router as execution_router
from app.api.workflow_routes import router as workflow_router
from app.api.plugin_routes import router as plugin_router
from app.api.scheduler_routes import router as scheduler_router
from app.api.dynamic_workflow_routes import router as dynamic_workflow_router
from app.services.scheduler_service import start_scheduler, stop_scheduler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler and restore persistent jobs on application startup
    start_scheduler()
    yield
    # Stop scheduler cleanly when application shuts down
    stop_scheduler()


app = FastAPI(
    title="Agentic Workflow Automation",
    description="An agent-based workflow automation system",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

app.include_router(workflow_router)
app.include_router(plugin_router)
app.include_router(execution_router)
app.include_router(scheduler_router)
app.include_router(dynamic_workflow_router)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health_check():
    return {"status": "healthy"}

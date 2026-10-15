from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from adapters.inbound.api.config_router import router as config_router
from adapters.inbound.api.customer_router import router as customer_router
from adapters.inbound.api.operator_router import router as operator_router
from adapters.outbound.default_configuration_adapter import DefaultConfigurationAdapter
from adapters.outbound.in_memory_container_repository import InMemoryContainerRepository
from adapters.outbound.log_alert_adapter import LogAlertAdapter
from adapters.outbound.log_display_adapter import LogDisplayAdapter
from domain.exceptions import (
    ExceedsMaxCapacity,
    InsufficientIngredient,
    MachineNotReady,
    RecipeNotFound,
    WasteContainerFullError,
)
from domain.model.machine import CoffeeMachine
from domain.model.value_objects import MachineState

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

CONFIG_PATH = Path(__file__).parent / "config" / "default_config.json"


def create_display():
    """Use the Sense HAT LED matrix when one is attached, otherwise just log."""
    try:
        from adapters.outbound.sense_hat_display_adapter import SenseHatDisplayAdapter

        return SenseHatDisplayAdapter(rotation=int(os.environ.get("SENSE_HAT_ROTATION", "0")))
    except (ImportError, OSError) as exc:
        logging.getLogger("coffee_machine.display").info(
            "Sense HAT not available (%s) — logging display output instead", exc
        )
        return LogDisplayAdapter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: wire all adapters and seed state ---
    config = DefaultConfigurationAdapter.load(CONFIG_PATH)
    container_repo = InMemoryContainerRepository.seed_from_config(config._config)
    machine = CoffeeMachine()
    machine.transition(MachineState.READY)
    alerts = LogAlertAdapter()
    display = create_display()
    display.show_ready()

    app.state.config = config
    app.state.container_repo = container_repo
    app.state.machine = machine
    app.state.alerts = alerts
    app.state.display = display

    yield
    # --- Shutdown: switch off the display ---
    display.close()


app = FastAPI(
    title="Virtual Coffee Machine",
    version="1.0.0",
    description="Digital twin of an automatic coffee machine — DDD + Ports & Adapters",
    lifespan=lifespan,
)

# --- Routers ---
app.include_router(customer_router, prefix="/api/v1")
app.include_router(operator_router, prefix="/api/v1")
app.include_router(config_router,   prefix="/api/v1")

# --- Status endpoint ---
@app.get("/api/v1/status", tags=["status"])
async def get_status(request: Request) -> dict:
    """Return current machine state."""
    return {"machine_state": request.app.state.machine.state.value}

# --- Static files + UI ---
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def serve_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


# --- Domain exception → HTTP response handlers ---

@app.exception_handler(MachineNotReady)
async def machine_not_ready_handler(request: Request, exc: MachineNotReady) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"error": "machine_not_ready", "machine_state": exc.current_state.value},
    )


@app.exception_handler(InsufficientIngredient)
async def insufficient_ingredient_handler(request: Request, exc: InsufficientIngredient) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "insufficient_ingredient",
            "container_id": exc.container_id.value,
            "required": exc.required.value,
            "available": exc.available.value,
            "unit": exc.required.unit,
        },
    )


@app.exception_handler(WasteContainerFullError)
async def waste_full_handler(request: Request, exc: WasteContainerFullError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "waste_container_full",
            "brew_count": exc.brew_count,
            "threshold": exc.threshold,
        },
    )


@app.exception_handler(ExceedsMaxCapacity)
async def exceeds_capacity_handler(request: Request, exc: ExceedsMaxCapacity) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "exceeds_max_capacity",
            "container_id": exc.container_id.value,
            "target": exc.target.value,
            "max_capacity": exc.max_capacity.value,
            "unit": exc.target.unit,
        },
    )


@app.exception_handler(RecipeNotFound)
async def recipe_not_found_handler(request: Request, exc: RecipeNotFound) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": "recipe_not_found", "beverage_id": exc.beverage_id},
    )

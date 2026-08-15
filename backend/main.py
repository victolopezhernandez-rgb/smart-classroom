import asyncio
import json
import sys
from pathlib import Path

# Allow imports from backend/ as root
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.classroom_state import classroom_state
from shared.broadcaster import register, unregister
from shared.logger import get_logger

from routes.twin_routes import router as twin_router
from routes.vision_routes import router as vision_router
from routes.light_sensor_routes import router as light_router
from routes.voice_routes import router as voice_router
from routes.orchestrator_routes import router as orchestrator_router
from routes.emergency_routes import router as emergency_router

logger = get_logger("Main")

app = FastAPI(title="Smart Classroom API", version="1.0.0")

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(twin_router)
app.include_router(vision_router)
app.include_router(light_router)
app.include_router(voice_router)
app.include_router(orchestrator_router)
app.include_router(emergency_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "Smart Classroom API is running"}


@app.get("/state")
def get_state():
    return classroom_state.to_dict()


@app.get("/health")
def health():
    return {"status": "healthy"}


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    register(websocket)
    logger.info("Browser client connected via WebSocket")
    try:
        # Send current state immediately on connect
        await websocket.send_text(
            json.dumps({"type": "STATE_UPDATE", "payload": classroom_state.to_dict()})
        )
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        unregister(websocket)
        logger.info("Browser client disconnected")


# ── Startup: launch the orchestrator decision loop ────────────────────────────

# Serve vendor scripts (React, Three.js, Babel) — no internet required
app.mount("/vendor", StaticFiles(directory="static/vendor"), name="vendor")
# Serve the frontend HTML
app.mount("/app", StaticFiles(directory="static", html=True), name="static")


@app.middleware("http")
async def no_cache_html(request, call_next):
    """Evita que el navegador guarde copias viejas del HTML (crítico en la feria)."""
    response = await call_next(request)
    if request.url.path.startswith("/app") or request.url.path == "/app":
        response.headers["Cache-Control"] = "no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.on_event("startup")
async def startup():
    logger.info("Smart Classroom backend starting up…")
    logger.info(f"Initial state: {classroom_state.to_dict()}")

    # Import here to avoid circular imports at module load time
    from agents.orchestrator import start_decision_loop
    asyncio.create_task(start_decision_loop())
    logger.info("Orchestrator decision loop launched")

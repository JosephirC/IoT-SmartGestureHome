"""Application FastAPI principale"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from services.mcp_service import shutdown_mcp
from routers import camera, devices


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: si tu veux initialiser des clients globaux, fais-le ici.
    yield
    # Shutdown: fermeture propre du client MCP si ouvert.
    await shutdown_mcp()


app = FastAPI(title="SmartHome API", version="1.0", lifespan=lifespan)

# Inclure les routers
app.include_router(camera.router)
app.include_router(devices.router)

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Retourne le dashboard HTML"""
    return FileResponse("static/dashboard.html")


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print("Démarrage du serveur sur http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

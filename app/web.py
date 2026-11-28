"""Entrada para servir Bizon y su API desde el mismo origen."""
from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

from app.api.v1.router import router as router_v1
from app.core.configuracion import configuracion


class FrontendBizon(StaticFiles):
    async def get_response(self, path, scope):
        ruta = Path(path)
        segmento = ruta.parts[0] if ruta.parts else ""
        if segmento == "api":
            raise HTTPException(404)
        try:
            return await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code != 404 or segmento == "assets" or ruta.suffix:
                raise
            # Las rutas directas del frontend las resuelve React Router.
            return await super().get_response("index.html", scope)


app = FastAPI(title=configuracion.nombre_app)
app.include_router(router_v1, prefix="/api/v1")


@app.get("/healthz", include_in_schema=False)
def estado():
    return {"app": configuracion.nombre_app, "estado": "ok"}


compilacion = Path(__file__).resolve().parents[1] / "frontend-ts" / "dist"
app.mount("/", FrontendBizon(directory=compilacion, html=True), name="frontend")

from fastapi import FastAPI

from app.api.v1.router import router as router_v1
from app.core.configuracion import configuracion

app = FastAPI(title=configuracion.nombre_app)

app.include_router(router_v1, prefix="/api/v1")


@app.get("/", tags=["Estado"])
def estado():
    return {"app": configuracion.nombre_app, "estado": "ok"}

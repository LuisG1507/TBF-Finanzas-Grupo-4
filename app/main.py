from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as router_v1
from app.core.configuracion import configuracion

app = FastAPI(title=configuracion.nombre_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_v1, prefix="/api/v1")


@app.get("/", tags=["Estado"])
def estado():
    return {"app": configuracion.nombre_app, "estado": "ok"}

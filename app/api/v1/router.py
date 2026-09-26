from fastapi import APIRouter

from app.api.v1.endpoints import endpoints_finanzas

router = APIRouter()

router.include_router(endpoints_finanzas.router)

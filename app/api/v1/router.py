from fastapi import APIRouter

from app.api.v1.endpoints import endpoints_finanzas, endpoints_pagos

router = APIRouter()

router.include_router(endpoints_finanzas.router)
router.include_router(endpoints_pagos.router)

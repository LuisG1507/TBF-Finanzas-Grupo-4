from fastapi import APIRouter

from app.api.v1.endpoints import endpoints_auth, endpoints_catalogos, endpoints_finanzas, endpoints_productos, endpoints_tiendas

router = APIRouter()

router.include_router(endpoints_auth.router)
router.include_router(endpoints_tiendas.router)
router.include_router(endpoints_catalogos.router)
router.include_router(endpoints_productos.router)
router.include_router(endpoints_finanzas.router)

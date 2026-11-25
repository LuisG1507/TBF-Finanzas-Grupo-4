from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencias import admin_de_negocio
from app.db.sesion import obtener_sesion
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_productos import ProductoActualizar, ProductoCrear, ProductoRespuesta
from app.services import servicio_productos

router = APIRouter(prefix="/productos", tags=["Productos y servicios"])


@router.post("", response_model=ProductoRespuesta, status_code=status.HTTP_201_CREATED, summary="Alta de un producto o servicio de tu tienda")
def crear_producto(datos: ProductoCrear, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_productos.crear(db, usuario.tienda_id, datos, usuario)


@router.get("", response_model=list[ProductoRespuesta], summary="Lista los productos de tu tienda")
def listar_productos(
    activo: bool | None = Query(default=None, description="true = solo activos, false = solo dados de baja"),
    buscar: str | None = Query(default=None, description="Texto a buscar en nombre, código o descripción"),
    marca_id: int | None = Query(default=None, gt=0),
    proveedor_id: int | None = Query(default=None, gt=0),
    permite_cuotas: bool | None = Query(default=None, description="true = solo los que se pueden pagar en cuotas"),
    permite_fin_de_mes: bool | None = Query(default=None, description="true = solo los que se pueden pagar a fin de mes"),
    limite: int = Query(default=50, ge=1, le=200),
    desplazamiento: int = Query(default=0, ge=0),
    usuario: UsuarioActual = Depends(admin_de_negocio),
    db: Session = Depends(obtener_sesion),
):
    return servicio_productos.listar(
        db, usuario.tienda_id, activo, buscar, marca_id, proveedor_id, permite_cuotas, permite_fin_de_mes, limite, desplazamiento
    )


@router.get("/{id_producto}", response_model=ProductoRespuesta, summary="Un producto de tu tienda")
def ver_producto(id_producto: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_productos.obtener(db, usuario.tienda_id, id_producto)


@router.patch("/{id_producto}", response_model=ProductoRespuesta, summary="Modifica un producto; solo cambia lo que se envía")
def modificar_producto(
    id_producto: int, datos: ProductoActualizar, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)
):
    return servicio_productos.actualizar(db, usuario.tienda_id, id_producto, datos, usuario)


@router.post("/{id_producto}/baja", response_model=ProductoRespuesta, summary="Da de baja un producto (deja de venderse, se conserva el historial)")
def dar_de_baja_producto(id_producto: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_productos.dar_de_baja(db, usuario.tienda_id, id_producto, usuario)


@router.post("/{id_producto}/alta", response_model=ProductoRespuesta, summary="Reactiva un producto dado de baja")
def reactivar_producto(id_producto: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_productos.reactivar(db, usuario.tienda_id, id_producto, usuario)

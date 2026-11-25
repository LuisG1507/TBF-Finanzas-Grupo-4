"""Unidades de medida, marcas y proveedores: los catálogos que usa el formulario de productos."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencias import admin_de_negocio, usuario_actual
from app.db.sesion import obtener_sesion
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_catalogos import (
    MarcaActualizar, MarcaCrear, MarcaRespuesta, MonedaRespuesta, ProveedorActualizar, ProveedorCrear, ProveedorRespuesta, UnidadRespuesta,
)
from app.services import servicio_catalogo

router = APIRouter(tags=["Catálogos de productos"])


# ---------------------------------------------------------------- unidades de medida

@router.get("/unidades-medida", response_model=list[UnidadRespuesta], summary="Unidades de medida disponibles (UND, KG, LT)")
def listar_unidades(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.listar_unidades(db)


@router.get("/monedas", response_model=list[MonedaRespuesta], summary="Monedas disponibles para el crédito de un cliente (PEN y USD)")
def listar_monedas(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.listar_monedas(db)


# ---------------------------------------------------------------- marcas

@router.post("/marcas", response_model=MarcaRespuesta, status_code=status.HTTP_201_CREATED, summary="Alta de una marca de tu tienda")
def crear_marca(datos: MarcaCrear, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.crear_marca(db, usuario.tienda_id, datos)


@router.get("/marcas", response_model=list[MarcaRespuesta], summary="Lista las marcas de tu tienda")
def listar_marcas(
    activo: bool | None = Query(default=None),
    buscar: str | None = Query(default=None),
    usuario: UsuarioActual = Depends(admin_de_negocio),
    db: Session = Depends(obtener_sesion),
):
    return servicio_catalogo.listar_marcas(db, usuario.tienda_id, activo, buscar)


@router.patch("/marcas/{id_marca}", response_model=MarcaRespuesta, summary="Cambia el nombre de una marca")
def modificar_marca(id_marca: int, datos: MarcaActualizar, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.actualizar_marca(db, usuario.tienda_id, id_marca, datos)


@router.post("/marcas/{id_marca}/baja", response_model=MarcaRespuesta, summary="Da de baja una marca")
def baja_marca(id_marca: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.cambiar_estado_marca(db, usuario.tienda_id, id_marca, activo=False)


@router.post("/marcas/{id_marca}/alta", response_model=MarcaRespuesta, summary="Reactiva una marca")
def alta_marca(id_marca: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.cambiar_estado_marca(db, usuario.tienda_id, id_marca, activo=True)


# ---------------------------------------------------------------- proveedores

@router.post("/proveedores", response_model=ProveedorRespuesta, status_code=status.HTTP_201_CREATED, summary="Alta de un proveedor de tu tienda")
def crear_proveedor(datos: ProveedorCrear, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.crear_proveedor(db, usuario.tienda_id, datos)


@router.get("/proveedores", response_model=list[ProveedorRespuesta], summary="Lista los proveedores de tu tienda")
def listar_proveedores(
    activo: bool | None = Query(default=None),
    buscar: str | None = Query(default=None, description="Texto a buscar en razón social o RUC"),
    usuario: UsuarioActual = Depends(admin_de_negocio),
    db: Session = Depends(obtener_sesion),
):
    return servicio_catalogo.listar_proveedores(db, usuario.tienda_id, activo, buscar)


@router.patch("/proveedores/{id_proveedor}", response_model=ProveedorRespuesta, summary="Modifica un proveedor; solo cambia lo que se envía")
def modificar_proveedor(
    id_proveedor: int, datos: ProveedorActualizar, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)
):
    return servicio_catalogo.actualizar_proveedor(db, usuario.tienda_id, id_proveedor, datos)


@router.post("/proveedores/{id_proveedor}/baja", response_model=ProveedorRespuesta, summary="Da de baja un proveedor")
def baja_proveedor(id_proveedor: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.cambiar_estado_proveedor(db, usuario.tienda_id, id_proveedor, activo=False)


@router.post("/proveedores/{id_proveedor}/alta", response_model=ProveedorRespuesta, summary="Reactiva un proveedor")
def alta_proveedor(id_proveedor: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_catalogo.cambiar_estado_proveedor(db, usuario.tienda_id, id_proveedor, activo=True)

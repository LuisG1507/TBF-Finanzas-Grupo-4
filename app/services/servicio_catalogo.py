"""Marcas, proveedores y unidades de medida de una tienda.

Todo se limita a la tienda de quien llama: pedir una marca o un proveedor de OTRA tienda responde 404,
igual que si no existiera (así no se revela qué hay en las demás tiendas).
Según la decisión 12 del equipo, la bitácora cubre tienda, producto, cliente, usuario, compra, pago y estado de
cuenta; las marcas y los proveedores son catálogos de apoyo y no se anotan.
"""
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.catalogo import Marca, Proveedor, UnidadMedida
from app.schemas.schemas_catalogos import MarcaActualizar, MarcaCrear, ProveedorActualizar, ProveedorCrear


def _conflicto(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, mensaje)


# ---------------------------------------------------------------- unidades de medida

def listar_unidades(db: Session) -> list[UnidadMedida]:
    return list(db.scalars(select(UnidadMedida).order_by(UnidadMedida.id_unidad)))


# ---------------------------------------------------------------- marcas

def marca_de_tienda(db: Session, tienda_id: int, id_marca: int) -> Marca:
    marca = db.scalar(select(Marca).where(Marca.id_marca == id_marca, Marca.tienda_id == tienda_id))
    if marca is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La marca no existe.")
    return marca


def _nombre_de_marca_libre(db: Session, tienda_id: int, nombre: str, excepto: int | None = None) -> None:
    consulta = select(Marca.id_marca).where(Marca.tienda_id == tienda_id, func.lower(Marca.nombre) == nombre.lower())
    if excepto is not None:
        consulta = consulta.where(Marca.id_marca != excepto)
    if db.scalar(consulta) is not None:
        raise _conflicto(f"Ya existe una marca llamada «{nombre}» en tu tienda.")


def listar_marcas(db: Session, tienda_id: int, activo: bool | None, buscar: str | None) -> list[Marca]:
    consulta = select(Marca).where(Marca.tienda_id == tienda_id).order_by(Marca.nombre)
    if activo is not None:
        consulta = consulta.where(Marca.activo == activo)
    if buscar:
        consulta = consulta.where(Marca.nombre.ilike(f"%{buscar.strip()}%"))
    return list(db.scalars(consulta))


def crear_marca(db: Session, tienda_id: int, datos: MarcaCrear) -> Marca:
    _nombre_de_marca_libre(db, tienda_id, datos.nombre)
    marca = Marca(tienda_id=tienda_id, nombre=datos.nombre)
    db.add(marca)
    db.commit()
    db.refresh(marca)
    return marca


def actualizar_marca(db: Session, tienda_id: int, id_marca: int, datos: MarcaActualizar) -> Marca:
    marca = marca_de_tienda(db, tienda_id, id_marca)
    if datos.nombre != marca.nombre:
        _nombre_de_marca_libre(db, tienda_id, datos.nombre, excepto=id_marca)
        marca.nombre = datos.nombre
        db.commit()
        db.refresh(marca)
    return marca


def cambiar_estado_marca(db: Session, tienda_id: int, id_marca: int, activo: bool) -> Marca:
    marca = marca_de_tienda(db, tienda_id, id_marca)
    if marca.activo == activo:
        raise _conflicto("La marca ya está activa." if activo else "La marca ya está dada de baja.")
    marca.activo = activo
    db.commit()
    db.refresh(marca)
    return marca


# ---------------------------------------------------------------- proveedores

def proveedor_de_tienda(db: Session, tienda_id: int, id_proveedor: int) -> Proveedor:
    proveedor = db.scalar(select(Proveedor).where(Proveedor.id_proveedor == id_proveedor, Proveedor.tienda_id == tienda_id))
    if proveedor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El proveedor no existe.")
    return proveedor


def _ruc_de_proveedor_libre(db: Session, tienda_id: int, ruc: str | None, excepto: int | None = None) -> None:
    if not ruc:
        return
    consulta = select(Proveedor.id_proveedor).where(Proveedor.tienda_id == tienda_id, Proveedor.ruc == ruc)
    if excepto is not None:
        consulta = consulta.where(Proveedor.id_proveedor != excepto)
    if db.scalar(consulta) is not None:
        raise _conflicto(f"Ya tienes un proveedor con el RUC {ruc}.")


def listar_proveedores(db: Session, tienda_id: int, activo: bool | None, buscar: str | None) -> list[Proveedor]:
    consulta = select(Proveedor).where(Proveedor.tienda_id == tienda_id).order_by(Proveedor.razon_social)
    if activo is not None:
        consulta = consulta.where(Proveedor.activo == activo)
    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(or_(Proveedor.razon_social.ilike(patron), Proveedor.ruc.ilike(patron)))
    return list(db.scalars(consulta))


def crear_proveedor(db: Session, tienda_id: int, datos: ProveedorCrear) -> Proveedor:
    _ruc_de_proveedor_libre(db, tienda_id, datos.ruc)
    proveedor = Proveedor(tienda_id=tienda_id, razon_social=datos.razon_social, ruc=datos.ruc, telefono=datos.telefono)
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


def actualizar_proveedor(db: Session, tienda_id: int, id_proveedor: int, datos: ProveedorActualizar) -> Proveedor:
    proveedor = proveedor_de_tienda(db, tienda_id, id_proveedor)
    cambios = datos.model_dump(exclude_unset=True)
    if "razon_social" in cambios and cambios["razon_social"] is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "«razon_social» no puede quedar vacío.")
    if "ruc" in cambios and cambios["ruc"] != proveedor.ruc:
        _ruc_de_proveedor_libre(db, tienda_id, cambios["ruc"], excepto=id_proveedor)
    for campo, valor in cambios.items():
        setattr(proveedor, campo, valor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


def cambiar_estado_proveedor(db: Session, tienda_id: int, id_proveedor: int, activo: bool) -> Proveedor:
    proveedor = proveedor_de_tienda(db, tienda_id, id_proveedor)
    if proveedor.activo == activo:
        raise _conflicto("El proveedor ya está activo." if activo else "El proveedor ya está dado de baja.")
    proveedor.activo = activo
    db.commit()
    db.refresh(proveedor)
    return proveedor

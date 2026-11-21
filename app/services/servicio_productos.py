"""Reglas de negocio de los productos y servicios de una tienda (enunciado, punto 2).

- Todo se limita a la tienda de quien llama (otra tienda = 404).
- El código es único DENTRO de la tienda, sin distinguir mayúsculas.
- Precio de lista (a crédito) >= precio de contado, y al menos una forma de pago permitida.
- Marca y proveedor deben ser de la misma tienda y no estar dados de baja.
- Baja lógica (`activo`): el producto deja de poder venderse pero se conserva para el historial de compras.
- Toda operación deja constancia en la bitácora.
"""
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.catalogo import Producto, UnidadMedida
from app.models.enumeraciones import AccionBitacora, EntidadBitacora
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_productos import (
    MarcaResumen, ProductoActualizar, ProductoCrear, ProductoRespuesta, ProveedorResumen, UnidadResumen,
)
from app.services import servicio_bitacora, servicio_catalogo

_NO_NULOS = {"codigo", "nombre", "unidad_id", "precio_contado", "precio_lista", "permite_fin_de_mes", "permite_cuotas"}


def _conflicto(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, mensaje)


def _invalido(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, mensaje)


def _respuesta(p: Producto) -> ProductoRespuesta:
    return ProductoRespuesta(
        id_producto=p.id_producto,
        codigo=p.codigo,
        nombre=p.nombre,
        descripcion=p.descripcion,
        imagen_url=p.imagen_url,
        unidad=UnidadResumen(id_unidad=p.unidad.id_unidad, codigo=p.unidad.codigo, nombre=p.unidad.nombre),
        marca=MarcaResumen(id_marca=p.marca.id_marca, nombre=p.marca.nombre) if p.marca is not None else None,
        proveedor=ProveedorResumen(id_proveedor=p.proveedor.id_proveedor, razon_social=p.proveedor.razon_social) if p.proveedor is not None else None,
        precio_contado=p.precio_contado,
        precio_lista=p.precio_lista,
        permite_fin_de_mes=p.permite_fin_de_mes,
        permite_cuotas=p.permite_cuotas,
        activo=p.activo,
    )


def _producto_de_tienda(db: Session, tienda_id: int, id_producto: int) -> Producto:
    producto = db.scalar(select(Producto).where(Producto.id_producto == id_producto, Producto.tienda_id == tienda_id))
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El producto no existe.")
    return producto


def _codigo_libre(db: Session, tienda_id: int, codigo: str, excepto: int | None = None) -> None:
    consulta = select(Producto.id_producto).where(Producto.tienda_id == tienda_id, func.lower(Producto.codigo) == codigo.lower())
    if excepto is not None:
        consulta = consulta.where(Producto.id_producto != excepto)
    if db.scalar(consulta) is not None:
        raise _conflicto(f"Ya tienes un producto con el código «{codigo}».")


def _validar_relaciones(db: Session, tienda_id: int, unidad_id: int | None, marca_id: int | None, proveedor_id: int | None) -> None:
    if unidad_id is not None and db.get(UnidadMedida, unidad_id) is None:
        raise _invalido("La unidad de medida no existe. Consulta GET /unidades-medida.")
    if marca_id is not None:
        try:
            marca = servicio_catalogo.marca_de_tienda(db, tienda_id, marca_id)
        except HTTPException:
            raise _invalido("La marca no existe en tu tienda.")
        if not marca.activo:
            raise _invalido("La marca está dada de baja.")
    if proveedor_id is not None:
        try:
            proveedor = servicio_catalogo.proveedor_de_tienda(db, tienda_id, proveedor_id)
        except HTTPException:
            raise _invalido("El proveedor no existe en tu tienda.")
        if not proveedor.activo:
            raise _invalido("El proveedor está dado de baja.")


def _plano(valor):
    """Convierte a algo que cabe en el JSON de la bitácora."""
    return str(valor) if isinstance(valor, Decimal) else valor


# ---------------------------------------------------------------- operaciones

def obtener(db: Session, tienda_id: int, id_producto: int) -> ProductoRespuesta:
    return _respuesta(_producto_de_tienda(db, tienda_id, id_producto))


def listar(
    db: Session,
    tienda_id: int,
    activo: bool | None,
    buscar: str | None,
    marca_id: int | None,
    proveedor_id: int | None,
    permite_cuotas: bool | None,
    permite_fin_de_mes: bool | None,
    limite: int,
    desplazamiento: int,
) -> list[ProductoRespuesta]:
    consulta = (
        select(Producto)
        .where(Producto.tienda_id == tienda_id)
        .options(selectinload(Producto.unidad), selectinload(Producto.marca), selectinload(Producto.proveedor))
        .order_by(Producto.nombre, Producto.id_producto)
    )
    if activo is not None:
        consulta = consulta.where(Producto.activo == activo)
    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(or_(Producto.nombre.ilike(patron), Producto.codigo.ilike(patron), Producto.descripcion.ilike(patron)))
    if marca_id is not None:
        consulta = consulta.where(Producto.marca_id == marca_id)
    if proveedor_id is not None:
        consulta = consulta.where(Producto.proveedor_id == proveedor_id)
    if permite_cuotas is not None:
        consulta = consulta.where(Producto.permite_cuotas == permite_cuotas)
    if permite_fin_de_mes is not None:
        consulta = consulta.where(Producto.permite_fin_de_mes == permite_fin_de_mes)
    return [_respuesta(p) for p in db.scalars(consulta.limit(limite).offset(desplazamiento))]


def crear(db: Session, tienda_id: int, datos: ProductoCrear, actor: UsuarioActual) -> ProductoRespuesta:
    _codigo_libre(db, tienda_id, datos.codigo)
    _validar_relaciones(db, tienda_id, datos.unidad_id, datos.marca_id, datos.proveedor_id)

    producto = Producto(tienda_id=tienda_id, **datos.model_dump())
    db.add(producto)
    db.flush()
    servicio_bitacora.registrar(
        db, actor.id_usuario, EntidadBitacora.PRODUCTO, producto.id_producto, AccionBitacora.ALTA,
        {"codigo": producto.codigo, "nombre": producto.nombre, "precio_contado": str(producto.precio_contado), "precio_lista": str(producto.precio_lista)},
    )
    db.commit()
    db.refresh(producto)
    return _respuesta(producto)


def actualizar(db: Session, tienda_id: int, id_producto: int, datos: ProductoActualizar, actor: UsuarioActual) -> ProductoRespuesta:
    producto = _producto_de_tienda(db, tienda_id, id_producto)
    cambios = datos.model_dump(exclude_unset=True)

    for campo in _NO_NULOS & cambios.keys():
        if cambios[campo] is None:
            raise _invalido(f"«{campo}» no puede quedar vacío.")

    # Las reglas que mezclan campos se comprueban con el resultado final (lo enviado + lo que ya había).
    contado = cambios.get("precio_contado", producto.precio_contado)
    lista = cambios.get("precio_lista", producto.precio_lista)
    if lista < contado:
        raise _invalido("El precio de lista (a crédito) no puede ser menor que el precio de contado.")
    if not (cambios.get("permite_fin_de_mes", producto.permite_fin_de_mes) or cambios.get("permite_cuotas", producto.permite_cuotas)):
        raise _invalido("El producto debe poder venderse a fin de mes, en cuotas, o en ambas formas.")

    if "codigo" in cambios and cambios["codigo"].lower() != producto.codigo.lower():
        _codigo_libre(db, tienda_id, cambios["codigo"], excepto=id_producto)
    _validar_relaciones(
        db, tienda_id,
        cambios.get("unidad_id") if cambios.get("unidad_id") != producto.unidad_id else None,
        cambios.get("marca_id") if cambios.get("marca_id") != producto.marca_id else None,
        cambios.get("proveedor_id") if cambios.get("proveedor_id") != producto.proveedor_id else None,
    )

    antes, despues = {}, {}
    for campo, valor in cambios.items():
        actual = getattr(producto, campo)
        if actual != valor:
            antes[campo], despues[campo] = _plano(actual), _plano(valor)
            setattr(producto, campo, valor)
    if not despues:
        return _respuesta(producto)

    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.PRODUCTO, producto.id_producto, AccionBitacora.MODIFICACION, {"antes": antes, "despues": despues})
    db.commit()
    db.refresh(producto)
    return _respuesta(producto)


def dar_de_baja(db: Session, tienda_id: int, id_producto: int, actor: UsuarioActual) -> ProductoRespuesta:
    producto = _producto_de_tienda(db, tienda_id, id_producto)
    if not producto.activo:
        raise _conflicto("El producto ya está dado de baja.")
    producto.activo = False
    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.PRODUCTO, producto.id_producto, AccionBitacora.BAJA, {"codigo": producto.codigo})
    db.commit()
    db.refresh(producto)
    return _respuesta(producto)


def reactivar(db: Session, tienda_id: int, id_producto: int, actor: UsuarioActual) -> ProductoRespuesta:
    producto = _producto_de_tienda(db, tienda_id, id_producto)
    if producto.activo:
        raise _conflicto("El producto ya está activo.")
    producto.activo = True
    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.PRODUCTO, producto.id_producto, AccionBitacora.MODIFICACION, {"activo": True, "motivo": "reactivación"})
    db.commit()
    db.refresh(producto)
    return _respuesta(producto)

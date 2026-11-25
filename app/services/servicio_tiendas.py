"""Reglas de negocio de las tiendas (administrador del sistema, punto 1 del enunciado).

- Alta: crea la tienda y el usuario de su administrador de negocio en UNA sola transacción
  (si algo falla no queda ni la tienda ni el usuario).
- Baja y reactivación son lógicas (`activo`): no se borra nada, para no perder el historial.
  Mientras la tienda está dada de baja, nadie de esa tienda puede entrar (lo comprueba el login).
- Toda operación deja una anotación en la bitácora.
"""
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.seguridad import hashear_password
from app.models.enumeraciones import AccionBitacora, EntidadBitacora, RolCodigo
from app.models.tienda import Tienda
from app.models.usuarios import Rol, Usuario
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_tiendas import AdministradorCreado, TiendaActualizar, TiendaCrear, TiendaCreadaRespuesta, TiendaRespuesta
from app.services import servicio_bitacora

_NO_NULOS = {"ruc", "razon_social", "nombre_comercial", "giro"}


def _conflicto(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, mensaje)


def obtener(db: Session, id_tienda: int) -> Tienda:
    tienda = db.get(Tienda, id_tienda)
    if tienda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La tienda no existe.")
    return tienda


def listar(db: Session, activo: bool | None, buscar: str | None, limite: int, desplazamiento: int) -> list[Tienda]:
    consulta = select(Tienda).order_by(Tienda.id_tienda)
    if activo is not None:
        consulta = consulta.where(Tienda.activo == activo)
    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(
            or_(Tienda.razon_social.ilike(patron), Tienda.nombre_comercial.ilike(patron), Tienda.ruc.ilike(patron), Tienda.giro.ilike(patron))
        )
    return list(db.scalars(consulta.limit(limite).offset(desplazamiento)))


def crear(db: Session, datos: TiendaCrear, actor: UsuarioActual) -> TiendaCreadaRespuesta:
    if db.scalar(select(Tienda.id_tienda).where(Tienda.ruc == datos.ruc)) is not None:
        raise _conflicto(f"Ya existe una tienda con el RUC {datos.ruc}.")
    if db.scalar(select(Usuario.id_usuario).where(Usuario.username == datos.admin_username)) is not None:
        raise _conflicto(f"El usuario «{datos.admin_username}» ya está en uso.")

    rol_admin = db.scalar(select(Rol).where(Rol.codigo == RolCodigo.ADMIN_NEG))
    if rol_admin is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Faltan los datos base: ejecuta los seeds (python -m app.db.seeds).")

    try:
        tienda = Tienda(
            ruc=datos.ruc,
            razon_social=datos.razon_social,
            nombre_comercial=datos.nombre_comercial,
            giro=datos.giro,
            direccion=datos.direccion,
            telefono=datos.telefono,
            email=datos.email,
        )
        db.add(tienda)
        db.flush()  # para conocer el id de la tienda

        administrador = Usuario(
            rol_id=rol_admin.id_rol,
            tienda_id=tienda.id_tienda,
            username=datos.admin_username,
            password_hash=hashear_password(datos.admin_password),
        )
        db.add(administrador)
        db.flush()

        servicio_bitacora.registrar(
            db, actor.id_usuario, EntidadBitacora.TIENDA, tienda.id_tienda, AccionBitacora.ALTA,
            {"ruc": tienda.ruc, "razon_social": tienda.razon_social, "giro": tienda.giro},
        )
        servicio_bitacora.registrar(
            db, actor.id_usuario, EntidadBitacora.USUARIO, administrador.id_usuario, AccionBitacora.ALTA,
            {"username": administrador.username, "rol": RolCodigo.ADMIN_NEG.value, "tienda_id": tienda.id_tienda},
        )
        db.commit()
    except IntegrityError:
        db.rollback()  # otra petición se adelantó con el mismo RUC o usuario
        raise _conflicto("El RUC o el usuario del administrador ya están registrados.")

    db.refresh(tienda)
    return TiendaCreadaRespuesta(
        tienda=TiendaRespuesta.model_validate(tienda),
        administrador=AdministradorCreado(id_usuario=administrador.id_usuario, username=administrador.username, rol=RolCodigo.ADMIN_NEG),
    )


def actualizar(db: Session, id_tienda: int, datos: TiendaActualizar, actor: UsuarioActual) -> Tienda:
    tienda = obtener(db, id_tienda)
    cambios = datos.model_dump(exclude_unset=True)

    for campo in _NO_NULOS & cambios.keys():
        if cambios[campo] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"«{campo}» no puede quedar vacío.")

    if "ruc" in cambios and cambios["ruc"] != tienda.ruc:
        if db.scalar(select(Tienda.id_tienda).where(Tienda.ruc == cambios["ruc"])) is not None:
            raise _conflicto(f"Ya existe otra tienda con el RUC {cambios['ruc']}.")

    antes, despues = {}, {}
    for campo, valor in cambios.items():
        if getattr(tienda, campo) != valor:
            antes[campo], despues[campo] = getattr(tienda, campo), valor
            setattr(tienda, campo, valor)
    if not despues:
        return tienda  # no cambió nada: no se anota

    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.TIENDA, tienda.id_tienda, AccionBitacora.MODIFICACION, {"antes": antes, "despues": despues})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflicto("El RUC ya está registrado en otra tienda.")
    db.refresh(tienda)
    return tienda


def dar_de_baja(db: Session, id_tienda: int, actor: UsuarioActual) -> Tienda:
    tienda = obtener(db, id_tienda)
    if not tienda.activo:
        raise _conflicto("La tienda ya está dada de baja.")
    tienda.activo = False
    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.TIENDA, tienda.id_tienda, AccionBitacora.BAJA, {"ruc": tienda.ruc})
    db.commit()
    db.refresh(tienda)
    return tienda


def reactivar(db: Session, id_tienda: int, actor: UsuarioActual) -> Tienda:
    tienda = obtener(db, id_tienda)
    if tienda.activo:
        raise _conflicto("La tienda ya está activa.")
    tienda.activo = True
    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.TIENDA, tienda.id_tienda, AccionBitacora.MODIFICACION, {"activo": True, "motivo": "reactivación"})
    db.commit()
    db.refresh(tienda)
    return tienda

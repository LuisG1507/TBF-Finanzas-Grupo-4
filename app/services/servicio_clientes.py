"""Reglas de negocio de los clientes de una tienda (administrador del negocio, punto 3 del enunciado).

- Todo se limita a la tienda de quien llama (otra tienda = 404).
- Alta: crea el usuario del cliente, el cliente y su condición de crédito en UNA transacción (todo o nada).
- El documento es único dentro de la tienda. El usuario de acceso es global: por defecto es el número de
  documento, y si ya lo usa otra persona (p. ej. el mismo vecino en otra tienda) se indica otro.
- La condición de crédito es VERSIONADA: cambiarla no pisa la anterior, la cierra (`vigente_hasta`) y abre una
  nueva. Cada compra queda ligada a la condición con la que se hizo, así que un cambio no altera compras viejas.
- Baja y reactivación lógicas (`activo`); un cliente dado de baja no puede entrar.
- Toda operación deja constancia en la bitácora (nunca contraseñas).
"""
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.seguridad import hashear_password
from app.core.tiempo import hoy_lima
from app.models.catalogo import Moneda
from app.models.cliente import Cliente, CondicionCredito
from app.models.enumeraciones import AccionBitacora, EntidadBitacora, RolCodigo
from app.models.enumeraciones import TipoTasa as TipoTasaModelo
from app.models.usuarios import Rol, Usuario
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_clientes import (
    ClienteActualizar, ClienteCrear, ClienteRespuesta, CondicionCrear, CondicionRespuesta, MonedaResumen, TasaPactadaRespuesta,
    TipoDocumento, validar_documento,
)
from app.services import servicio_bitacora
from app.services.finance.finance_tasas import TipoTasa

_NO_NULOS = {"tipo_documento", "numero_documento", "nombres", "apellidos"}


def _conflicto(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, mensaje)


def _invalido(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, mensaje)


# ---------------------------------------------------------------- armado de respuestas

def _tasa(tipo: TipoTasaModelo, tasa, plazo_dias: int, capitalizacion_dias: int | None) -> TasaPactadaRespuesta:
    return TasaPactadaRespuesta(tipo=TipoTasa(tipo.value), tasa_pct=tasa, plazo_dias=plazo_dias, capitalizacion_dias=capitalizacion_dias)


def _condicion_respuesta(c: CondicionCredito) -> CondicionRespuesta:
    return CondicionRespuesta(
        id_condicion=c.id_condicion,
        moneda=MonedaResumen(codigo_iso=c.moneda.codigo_iso, simbolo=c.moneda.simbolo),
        tasa_compensatoria=_tasa(c.tipo_tasa_comp, c.tasa_compensatoria, c.plazo_tasa_comp_dias, c.capitaliz_comp_dias),
        tasa_moratoria=_tasa(c.tipo_tasa_mora, c.tasa_moratoria, c.plazo_tasa_mora_dias, c.capitaliz_mora_dias),
        limite_credito=c.limite_credito,
        max_meses=c.max_meses,
        dia_corte=c.dia_corte,
        hora_corte=c.hora_corte,
        dia_pago=c.dia_pago,
        vigente_desde=c.vigente_desde,
        vigente_hasta=c.vigente_hasta,
    )


def condicion_vigente(cliente: Cliente) -> CondicionCredito | None:
    vigentes = [c for c in cliente.condiciones_credito if c.vigente_hasta is None]
    return max(vigentes, key=lambda c: c.id_condicion) if vigentes else None


def _respuesta(cliente: Cliente) -> ClienteRespuesta:
    vigente = condicion_vigente(cliente)
    return ClienteRespuesta(
        id_cliente=cliente.id_cliente,
        tipo_documento=cliente.tipo_documento,
        numero_documento=cliente.numero_documento,
        nombres=cliente.nombres,
        apellidos=cliente.apellidos,
        direccion=cliente.direccion,
        telefono=cliente.telefono,
        email=cliente.email,
        activo=cliente.activo,
        fecha_registro=cliente.fecha_registro,
        usuario=cliente.usuario.username,
        condicion=_condicion_respuesta(vigente) if vigente is not None else None,
    )


def _detalle_condicion(c: CondicionCredito) -> dict:
    """Resumen de una condición para la bitácora (todo como texto o número simple)."""
    return {
        "moneda": c.moneda.codigo_iso,
        "tasa_compensatoria": f"{c.tasa_compensatoria} % {c.tipo_tasa_comp.value} plazo {c.plazo_tasa_comp_dias} d cap {c.capitaliz_comp_dias}",
        "tasa_moratoria": f"{c.tasa_moratoria} % {c.tipo_tasa_mora.value} plazo {c.plazo_tasa_mora_dias} d cap {c.capitaliz_mora_dias}",
        "limite_credito": str(c.limite_credito),
        "max_meses": c.max_meses,
        "dia_corte": c.dia_corte,
        "hora_corte": c.hora_corte.isoformat(),
        "dia_pago": c.dia_pago,
    }


# ---------------------------------------------------------------- búsquedas

def _consulta_clientes(tienda_id: int):
    return (
        select(Cliente)
        .where(Cliente.tienda_id == tienda_id)
        .options(selectinload(Cliente.usuario), selectinload(Cliente.condiciones_credito).selectinload(CondicionCredito.moneda))
    )


def _cliente_de_tienda(db: Session, tienda_id: int, id_cliente: int, *, bloquear: bool = False) -> Cliente:
    consulta = _consulta_clientes(tienda_id).where(Cliente.id_cliente == id_cliente)
    if bloquear:
        consulta = consulta.with_for_update()
    cliente = db.scalar(consulta)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El cliente no existe.")
    return cliente


cliente_de_tienda = _cliente_de_tienda  # lo usa el módulo de compras


def condicion_en_fecha(cliente: Cliente, fecha) -> CondicionCredito | None:
    """La condición de crédito que regía en una fecha (para compras registradas con fecha pasada)."""
    candidatas = [c for c in cliente.condiciones_credito if c.vigente_desde <= fecha and (c.vigente_hasta is None or fecha <= c.vigente_hasta)]
    return max(candidatas, key=lambda c: c.id_condicion) if candidatas else None


def _fecha_de_inicio(pedida, hoy):
    if pedida is None:
        return hoy
    if pedida > hoy:
        raise _invalido("La fecha de inicio de la condición no puede ser futura.")
    return pedida


def _documento_libre(db: Session, tienda_id: int, tipo: str, numero: str, excepto: int | None = None) -> None:
    consulta = select(Cliente.id_cliente).where(Cliente.tienda_id == tienda_id, Cliente.tipo_documento == tipo, Cliente.numero_documento == numero)
    if excepto is not None:
        consulta = consulta.where(Cliente.id_cliente != excepto)
    if db.scalar(consulta) is not None:
        raise _conflicto(f"Ya tienes un cliente con {tipo} {numero}.")


def _moneda(db: Session, codigo: str) -> Moneda:
    moneda = db.scalar(select(Moneda).where(Moneda.codigo_iso == codigo))
    if moneda is None:
        raise _invalido(f"La moneda «{codigo}» no existe. Consulta GET /monedas.")
    return moneda


def _construir_condicion(id_cliente: int, moneda: Moneda, c: CondicionCrear, desde) -> CondicionCredito:
    return CondicionCredito(
        cliente_id=id_cliente,
        moneda_id=moneda.id_moneda,
        tasa_compensatoria=c.tasa_compensatoria.tasa_pct,
        tipo_tasa_comp=TipoTasaModelo(c.tasa_compensatoria.tipo.value),
        plazo_tasa_comp_dias=c.tasa_compensatoria.plazo_dias,
        capitaliz_comp_dias=c.tasa_compensatoria.capitalizacion_dias,
        tasa_moratoria=c.tasa_moratoria.tasa_pct,
        tipo_tasa_mora=TipoTasaModelo(c.tasa_moratoria.tipo.value),
        plazo_tasa_mora_dias=c.tasa_moratoria.plazo_dias,
        capitaliz_mora_dias=c.tasa_moratoria.capitalizacion_dias,
        limite_credito=c.limite_credito,
        max_meses=c.max_meses,
        dia_corte=c.dia_corte,
        hora_corte=c.hora_corte,
        dia_pago=c.dia_pago,
        vigente_desde=desde,
        vigente_hasta=None,
    )


_CAMPOS_CONDICION = (
    "moneda_id", "tasa_compensatoria", "tipo_tasa_comp", "plazo_tasa_comp_dias", "capitaliz_comp_dias",
    "tasa_moratoria", "tipo_tasa_mora", "plazo_tasa_mora_dias", "capitaliz_mora_dias",
    "limite_credito", "max_meses", "dia_corte", "hora_corte", "dia_pago",
)


def _son_iguales(a: CondicionCredito, b: CondicionCredito) -> bool:
    return all(getattr(a, campo) == getattr(b, campo) for campo in _CAMPOS_CONDICION)


# ---------------------------------------------------------------- operaciones

def obtener(db: Session, tienda_id: int, id_cliente: int) -> ClienteRespuesta:
    return _respuesta(_cliente_de_tienda(db, tienda_id, id_cliente))


def listar(db: Session, tienda_id: int, activo: bool | None, buscar: str | None, limite: int, desplazamiento: int) -> list[ClienteRespuesta]:
    consulta = _consulta_clientes(tienda_id).order_by(Cliente.apellidos, Cliente.nombres, Cliente.id_cliente)
    if activo is not None:
        consulta = consulta.where(Cliente.activo == activo)
    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(or_(
            (Cliente.nombres + " " + Cliente.apellidos).ilike(patron),
            (Cliente.apellidos + " " + Cliente.nombres).ilike(patron),
            Cliente.numero_documento.ilike(patron),
        ))
    return [_respuesta(c) for c in db.scalars(consulta.limit(limite).offset(desplazamiento))]


def crear(db: Session, tienda_id: int, datos: ClienteCrear, actor: UsuarioActual) -> ClienteRespuesta:
    tipo = datos.tipo_documento.value
    _documento_libre(db, tienda_id, tipo, datos.numero_documento)

    username = datos.usuario or datos.numero_documento
    if db.scalar(select(Usuario.id_usuario).where(Usuario.username == username)) is not None:
        raise _conflicto(f"El usuario «{username}» ya está en uso. Indica otro en el campo «usuario».")
    moneda = _moneda(db, datos.condicion.moneda)
    desde = _fecha_de_inicio(datos.condicion.vigente_desde, hoy_lima())
    rol = db.scalar(select(Rol).where(Rol.codigo == RolCodigo.CLIENTE))
    if rol is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Faltan los datos base: ejecuta los seeds (python -m app.db.seeds).")

    try:
        usuario = Usuario(rol_id=rol.id_rol, tienda_id=tienda_id, username=username, password_hash=hashear_password(datos.password))
        db.add(usuario)
        db.flush()
        cliente = Cliente(
            tienda_id=tienda_id, usuario_id=usuario.id_usuario, tipo_documento=tipo, numero_documento=datos.numero_documento,
            nombres=datos.nombres, apellidos=datos.apellidos, direccion=datos.direccion, telefono=datos.telefono, email=datos.email,
        )
        db.add(cliente)
        db.flush()
        condicion = _construir_condicion(cliente.id_cliente, moneda, datos.condicion, desde)
        db.add(condicion)
        db.flush()

        servicio_bitacora.registrar(
            db, actor.id_usuario, EntidadBitacora.CLIENTE, cliente.id_cliente, AccionBitacora.ALTA,
            {"documento": f"{tipo} {cliente.numero_documento}", "usuario": username, "condicion": _detalle_condicion(condicion)},
        )
        servicio_bitacora.registrar(
            db, actor.id_usuario, EntidadBitacora.USUARIO, usuario.id_usuario, AccionBitacora.ALTA,
            {"username": username, "rol": RolCodigo.CLIENTE.value, "tienda_id": tienda_id},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflicto("El documento o el usuario ya están registrados.")

    return _respuesta(_cliente_de_tienda(db, tienda_id, cliente.id_cliente))


def actualizar(db: Session, tienda_id: int, id_cliente: int, datos: ClienteActualizar, actor: UsuarioActual) -> ClienteRespuesta:
    cliente = _cliente_de_tienda(db, tienda_id, id_cliente)
    cambios = datos.model_dump(exclude_unset=True)
    for campo in _NO_NULOS & cambios.keys():
        if cambios[campo] is None:
            raise _invalido(f"«{campo}» no puede quedar vacío.")

    if "tipo_documento" in cambios or "numero_documento" in cambios:
        tipo = cambios.get("tipo_documento") or TipoDocumento(cliente.tipo_documento)
        try:
            numero = validar_documento(tipo, cambios.get("numero_documento", cliente.numero_documento))
        except ValueError as error:
            raise _invalido(str(error))
        cambios["tipo_documento"], cambios["numero_documento"] = tipo.value, numero
        if (tipo.value, numero) != (cliente.tipo_documento, cliente.numero_documento):
            _documento_libre(db, tienda_id, tipo.value, numero, excepto=id_cliente)

    antes, despues = {}, {}
    for campo, valor in cambios.items():
        if getattr(cliente, campo) != valor:
            antes[campo], despues[campo] = getattr(cliente, campo), valor
            setattr(cliente, campo, valor)
    if not despues:
        return _respuesta(cliente)

    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.CLIENTE, cliente.id_cliente, AccionBitacora.MODIFICACION, {"antes": antes, "despues": despues})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflicto("Ya tienes otro cliente con ese documento.")
    return _respuesta(_cliente_de_tienda(db, tienda_id, id_cliente))


def cambiar_condicion(db: Session, tienda_id: int, id_cliente: int, datos: CondicionCrear, actor: UsuarioActual) -> ClienteRespuesta:
    from app.services.servicio_compras import capital_pendiente

    cliente = _cliente_de_tienda(db, tienda_id, id_cliente, bloquear=True)
    if not cliente.activo:
        raise _conflicto("El cliente está dado de baja: reactívalo antes de cambiar sus condiciones.")

    moneda = _moneda(db, datos.moneda)
    desde = _fecha_de_inicio(datos.vigente_desde, hoy_lima())
    nueva = _construir_condicion(cliente.id_cliente, moneda, datos, desde)
    nueva.moneda = moneda
    anterior = condicion_vigente(cliente)
    if anterior is not None and _son_iguales(anterior, nueva):
        return _respuesta(cliente)  # no cambió nada: no se crea una versión nueva
    if anterior is not None and desde < anterior.vigente_desde:
        raise _invalido("La nueva condición no puede empezar antes que la que está vigente.")

    if anterior is not None:
        if anterior.moneda_id != moneda.id_moneda:
            pendiente = capital_pendiente(db, id_cliente, anterior.moneda.codigo_iso)
            if pendiente > 0:
                raise _conflicto(
                    f"No se puede cambiar la moneda del crédito mientras haya capital pendiente "
                    f"({anterior.moneda.simbolo} {pendiente})."
                )
        anterior.vigente_hasta = desde - timedelta(days=1)  # la anterior deja de regir el día antes de la nueva
    db.add(nueva)
    db.flush()
    servicio_bitacora.registrar(
        db, actor.id_usuario, EntidadBitacora.CLIENTE, cliente.id_cliente, AccionBitacora.MODIFICACION,
        {"condicion": {"antes": _detalle_condicion(anterior) if anterior is not None else None, "despues": _detalle_condicion(nueva)}},
    )
    db.commit()
    return _respuesta(_cliente_de_tienda(db, tienda_id, id_cliente))


def historial_condiciones(db: Session, tienda_id: int, id_cliente: int) -> list[CondicionRespuesta]:
    cliente = _cliente_de_tienda(db, tienda_id, id_cliente)
    ordenadas = sorted(cliente.condiciones_credito, key=lambda c: (c.vigente_desde, c.id_condicion), reverse=True)
    return [_condicion_respuesta(c) for c in ordenadas]


def dar_de_baja(db: Session, tienda_id: int, id_cliente: int, actor: UsuarioActual) -> ClienteRespuesta:
    from app.services.moneda import PEN
    from app.services.servicio_compras import capital_pendiente

    cliente = _cliente_de_tienda(db, tienda_id, id_cliente, bloquear=True)
    if not cliente.activo:
        raise _conflicto("El cliente ya está dado de baja.")
    condicion = condicion_vigente(cliente)
    moneda = condicion.moneda.codigo_iso if condicion is not None else PEN
    pendiente = capital_pendiente(db, id_cliente, moneda)
    if pendiente > 0:
        raise _conflicto(f"El cliente tiene deuda pendiente ({moneda} {pendiente}) y no se puede dar de baja.")
    cliente.activo = False
    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.CLIENTE, cliente.id_cliente, AccionBitacora.BAJA, {"documento": f"{cliente.tipo_documento} {cliente.numero_documento}"})
    db.commit()
    return _respuesta(_cliente_de_tienda(db, tienda_id, id_cliente))


def reactivar(db: Session, tienda_id: int, id_cliente: int, actor: UsuarioActual) -> ClienteRespuesta:
    cliente = _cliente_de_tienda(db, tienda_id, id_cliente)
    if cliente.activo:
        raise _conflicto("El cliente ya está activo.")
    cliente.activo = True
    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.CLIENTE, cliente.id_cliente, AccionBitacora.MODIFICACION, {"activo": True, "motivo": "reactivación"})
    db.commit()
    return _respuesta(_cliente_de_tienda(db, tienda_id, id_cliente))


def reiniciar_password(db: Session, tienda_id: int, id_cliente: int, nueva_password: str, actor: UsuarioActual) -> None:
    cliente = _cliente_de_tienda(db, tienda_id, id_cliente)
    cliente.usuario.password_hash = hashear_password(nueva_password)
    servicio_bitacora.registrar(db, actor.id_usuario, EntidadBitacora.USUARIO, cliente.usuario_id, AccionBitacora.MODIFICACION, {"campo": "contraseña", "cliente_id": cliente.id_cliente})
    db.commit()


def mi_perfil(db: Session, tienda_id: int, id_cliente: int) -> ClienteRespuesta:
    return _respuesta(_cliente_de_tienda(db, tienda_id, id_cliente))

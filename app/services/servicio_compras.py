"""Compras a crédito de los clientes de una tienda (administrador del negocio; enunciado, puntos 4, 5 y 6).

Cómo se calcula una compra
--------------------------
1. Los precios salen del PRECIO DE LISTA (a crédito) de cada producto y se entienden en soles. Si el crédito del cliente
   es en dólares, cada precio unitario se convierte (soles ÷ tipo de cambio) y se redondea a 2 decimales; ese precio
   queda CONGELADO en el detalle. Subtotal = precio unitario × cantidad (2 decimales); total = suma de subtotales.
2. La condición de crédito que rige es la vigente EN LA FECHA de la compra, y la compra queda ligada a ella.
   Si la moneda de ese pacto ya cambió, no se admite registrar una compra retroactiva en la moneda anterior.
3. Ciclo (ver ciclo_credito.py): fecha de corte, fecha de pago del ciclo y días de gracia (30/360).
4. CUOTAS: método francés con la gracia capitalizada (C' = C·(1+TEP)^(días/30)); la primera cuota vence un mes después
   de la fecha de pago del ciclo. FIN_DE_MES: un solo pago en la fecha de pago del ciclo, por el capital capitalizado
   hasta esa fecha (es decir, con los intereses de los días entre la compra y el pago); no genera filas de cuota.
5. LÍMITE (decisión 3): compra + capital pendiente del cliente <= límite de crédito. El capital pendiente son los
   montos de las compras a fin de mes vigentes más las amortizaciones de las cuotas aún no pagadas, todo llevado a la
   moneda del crédito. No cuentan los intereses por cobrar.

Todo se limita a la tienda de quien llama. Cada operación deja constancia en la bitácora.
"""
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.tiempo import ZONA_LIMA, ahora_lima
from app.models.catalogo import Producto
from app.models.cliente import Cliente, CondicionCredito
from app.models.compra import Compra, Cuota, DetalleCompra
from app.models.enumeraciones import AccionBitacora, EntidadBitacora, EstadoCompra, EstadoCuota, ModalidadCompra
from app.models.estado_cuenta import EstadoCuenta, EstadoCuentaDetalle
from app.models.pago import Pago
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_clientes import MonedaResumen
from app.schemas.schemas_compras import (
    ClienteResumenCompra, CompraCrear, CompraResumen, CompraRespuesta, CreditoDisponibleRespuesta, CreditoRespuesta, CuotaRespuesta,
    ItemCompraRespuesta,
)
from app.services import ciclo_credito, servicio_bitacora, servicio_clientes
from app.services.finance import finance_amortizacion as amortizacion
from app.services.finance.finance_amortizacion import PlanFrances
from app.services.finance.finance_tasas import DECIMALES_MONTO, TipoTasa, redondear
from app.services.moneda import PEN, convertir

PERIODO_DE_PAGO_DIAS = 30  # las cuotas son mensuales (meses de 30 días)


def _invalido(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, mensaje)


def _conflicto(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, mensaje)


@dataclass
class _Borrador:
    """Todo lo que se calcula de una compra antes de guardarla."""

    cliente: Cliente
    condicion: CondicionCredito
    fecha_hora: datetime
    modalidad: ModalidadCompra
    lineas: list  # (producto, cantidad, precio_unitario, subtotal)
    monto_total: Decimal
    fecha_corte: date
    fecha_pago_ciclo: date
    dias_gracia: int
    tep_pct: Decimal
    capital_capitalizado: Decimal
    num_cuotas: int
    plan: PlanFrances | None
    fechas_cuotas: list[date]
    limite: Decimal
    capital_pendiente: Decimal

    @property
    def credito_disponible(self) -> Decimal:
        return max(self.limite - self.capital_pendiente, Decimal(0))

    @property
    def excede_limite(self) -> bool:
        return self.monto_total > self.limite - self.capital_pendiente

    @property
    def fecha_primer_pago(self) -> date:
        return self.fechas_cuotas[0] if self.plan is not None else self.fecha_pago_ciclo

    @property
    def total_a_pagar(self) -> Decimal:
        return self.plan.total_a_pagar if self.plan is not None else self.capital_capitalizado


# ---------------------------------------------------------------- armado de respuestas

def _cliente_resumen(c: Cliente) -> ClienteResumenCompra:
    return ClienteResumenCompra(id_cliente=c.id_cliente, nombre=f"{c.nombres} {c.apellidos}", documento=f"{c.tipo_documento} {c.numero_documento}")


def _respuesta_de_borrador(b: _Borrador) -> CompraRespuesta:
    cronograma = []
    if b.plan is not None:
        cronograma = [
            CuotaRespuesta(
                numero=f.numero, fecha_vencimiento=b.fechas_cuotas[f.numero - 1], saldo_inicial=f.saldo_inicial, interes=f.interes,
                amortizacion=f.amortizacion, monto_cuota=f.cuota, saldo_final=f.saldo_final, estado=EstadoCuota.PENDIENTE,
            )
            for f in b.plan.cronograma
        ]
    return CompraRespuesta(
        id_compra=None,
        estado=None,
        id_condicion=b.condicion.id_condicion,
        cliente=_cliente_resumen(b.cliente),
        fecha_hora_compra=b.fecha_hora,
        modalidad=b.modalidad,
        moneda=MonedaResumen(codigo_iso=b.condicion.moneda.codigo_iso, simbolo=b.condicion.moneda.simbolo),
        items=[
            ItemCompraRespuesta(producto_id=p.id_producto, codigo=p.codigo, nombre=p.nombre, cantidad=cant, precio_unitario=precio, subtotal=sub)
            for p, cant, precio, sub in b.lineas
        ],
        monto_total=b.monto_total,
        fecha_corte=b.fecha_corte,
        dias_gracia=b.dias_gracia,
        tep_aplicada=b.tep_pct,
        capital_capitalizado=b.capital_capitalizado,
        interes_gracia=b.capital_capitalizado - b.monto_total,
        num_cuotas=b.num_cuotas,
        cuota=b.plan.cuota if b.plan is not None else None,
        fecha_primer_pago=b.fecha_primer_pago,
        total_intereses=b.total_a_pagar - b.monto_total,
        total_a_pagar=b.total_a_pagar,
        cronograma=cronograma,
        credito=CreditoRespuesta(
            limite_credito=b.limite, capital_pendiente=b.capital_pendiente, credito_disponible=b.credito_disponible, excede_limite=b.excede_limite
        ),
    )


def _total_a_pagar(compra: Compra) -> Decimal:
    if compra.modalidad == ModalidadCompra.CUOTAS:
        return sum((q.monto_cuota for q in compra.cuotas), Decimal(0))
    return compra.capital_capitalizado


def _respuesta_de_compra(compra: Compra) -> CompraRespuesta:
    cuotas = sorted(compra.cuotas, key=lambda q: q.numero_cuota)
    total = _total_a_pagar(compra)
    moneda = compra.condicion.moneda
    return CompraRespuesta(
        id_compra=compra.id_compra,
        estado=compra.estado,
        id_condicion=compra.condicion_id,
        cliente=_cliente_resumen(compra.cliente),
        fecha_hora_compra=compra.fecha_hora_compra,
        modalidad=compra.modalidad,
        moneda=MonedaResumen(codigo_iso=moneda.codigo_iso, simbolo=moneda.simbolo),
        items=[
            ItemCompraRespuesta(
                producto_id=d.producto_id, codigo=d.producto.codigo, nombre=d.producto.nombre, cantidad=d.cantidad,
                precio_unitario=d.precio_unitario, subtotal=d.subtotal,
            )
            for d in sorted(compra.detalles, key=lambda d: d.id_detalle)
        ],
        monto_total=compra.monto_total,
        fecha_corte=compra.fecha_corte_asignada,
        dias_gracia=compra.dias_gracia,
        tep_aplicada=compra.tep_aplicada,
        capital_capitalizado=compra.capital_capitalizado,
        interes_gracia=compra.capital_capitalizado - compra.monto_total,
        num_cuotas=compra.num_cuotas,
        cuota=cuotas[0].monto_cuota if cuotas else None,
        fecha_primer_pago=compra.fecha_primer_pago,
        total_intereses=total - compra.monto_total,
        total_a_pagar=total,
        cronograma=[
            CuotaRespuesta(
                numero=q.numero_cuota, fecha_vencimiento=q.fecha_vencimiento, saldo_inicial=q.saldo_inicial, interes=q.interes,
                amortizacion=q.amortizacion, monto_cuota=q.monto_cuota, saldo_final=q.saldo_final, estado=q.estado,
            )
            for q in cuotas
        ],
    )


def _opciones_de_carga():
    return (
        selectinload(Compra.cliente),
        selectinload(Compra.condicion).selectinload(CondicionCredito.moneda),
        selectinload(Compra.detalles).selectinload(DetalleCompra.producto),
        selectinload(Compra.cuotas),
    )


def _compra_de_tienda(db: Session, tienda_id: int, id_compra: int) -> Compra:
    compra = db.scalar(
        select(Compra).join(Cliente, Cliente.id_cliente == Compra.cliente_id)
        .where(Compra.id_compra == id_compra, Cliente.tienda_id == tienda_id).options(*_opciones_de_carga())
    )
    if compra is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La compra no existe.")
    return compra


# ---------------------------------------------------------------- crédito del cliente

def capital_pendiente(db: Session, id_cliente: int, moneda_destino: str) -> Decimal:
    """Capital que el cliente debe hoy (sin intereses por cobrar), llevado a `moneda_destino`."""
    compras = db.scalars(
        select(Compra).where(Compra.cliente_id == id_cliente, Compra.estado == EstadoCompra.VIGENTE)
        .options(selectinload(Compra.cuotas), selectinload(Compra.condicion).selectinload(CondicionCredito.moneda))
    )
    return sumar_capital_pendiente(compras, moneda_destino)


def sumar_capital_pendiente(compras: Iterable[Compra], moneda_destino: str) -> Decimal:
    total = Decimal(0)
    for c in compras:
        if c.estado != EstadoCompra.VIGENTE:
            continue
        if c.modalidad == ModalidadCompra.CUOTAS:
            capital = sum((q.amortizacion for q in c.cuotas if q.estado != EstadoCuota.PAGADA), Decimal(0))
        else:
            capital = c.monto_total
        total += convertir(capital, c.condicion.moneda.codigo_iso, moneda_destino)
    return redondear(total, DECIMALES_MONTO)


def credito_disponible(db: Session, tienda_id: int, id_cliente: int) -> CreditoDisponibleRespuesta:
    cliente = servicio_clientes.cliente_de_tienda(db, tienda_id, id_cliente)
    condicion = servicio_clientes.condicion_vigente(cliente)
    if condicion is None:
        raise _conflicto("El cliente no tiene una condición de crédito vigente.")
    pendiente = capital_pendiente(db, id_cliente, condicion.moneda.codigo_iso)
    return CreditoDisponibleRespuesta(
        moneda=MonedaResumen(codigo_iso=condicion.moneda.codigo_iso, simbolo=condicion.moneda.simbolo),
        limite_credito=condicion.limite_credito,
        capital_pendiente=pendiente,
        credito_disponible=max(condicion.limite_credito - pendiente, Decimal(0)),
    )


# ---------------------------------------------------------------- cálculo

def _fecha_hora_local(pedida: datetime | None) -> datetime:
    ahora = ahora_lima()
    if pedida is None:
        return ahora
    local = pedida.replace(tzinfo=ZONA_LIMA) if pedida.tzinfo is None else pedida.astimezone(ZONA_LIMA)
    if local > ahora:
        raise _invalido("La fecha y hora de la compra no pueden ser futuras.")
    return local


def _validar_cortes_abiertos(db: Session, cliente_id: int, corte: date, cuotas: int) -> None:
    cortes = [ciclo_credito.sumar_meses(corte, mes) for mes in range(cuotas + 1)]
    corte_emitido = db.scalar(
        select(EstadoCuenta.fecha_corte).where(EstadoCuenta.cliente_id == cliente_id, EstadoCuenta.fecha_corte.in_(cortes))
        .order_by(EstadoCuenta.fecha_corte).limit(1)
    )
    if corte_emitido is not None:
        raise _conflicto(f"El corte del {corte_emitido.isoformat()} ya tiene un estado de cuenta emitido.")


def _calcular(db: Session, tienda_id: int, datos: CompraCrear, *, bloquear_cliente: bool = False) -> _Borrador:
    cliente = servicio_clientes.cliente_de_tienda(db, tienda_id, datos.cliente_id, bloquear=bloquear_cliente)
    if not cliente.activo:
        raise _conflicto("El cliente está dado de baja: no se le pueden registrar compras.")

    fecha_hora = _fecha_hora_local(datos.fecha_hora_compra)
    condicion = servicio_clientes.condicion_en_fecha(cliente, fecha_hora.date())
    if condicion is None:
        raise _invalido(f"El cliente no tenía una condición de crédito vigente el {fecha_hora.date().isoformat()}.")
    vigente = servicio_clientes.condicion_vigente(cliente)
    if vigente is not None and condicion.moneda_id != vigente.moneda_id:
        raise _conflicto(f"La compra corresponde a la moneda anterior ({condicion.moneda.codigo_iso}) del crédito del cliente.")
    moneda = condicion.moneda.codigo_iso

    # --- productos
    ids = [i.producto_id for i in datos.items]
    if len(set(ids)) != len(ids):
        raise _invalido("Un producto aparece más de una vez: suma sus cantidades en una sola línea.")
    productos = {p.id_producto: p for p in db.scalars(select(Producto).where(Producto.tienda_id == tienda_id, Producto.id_producto.in_(ids)))}
    lineas, monto_total = [], Decimal(0)
    for item in datos.items:
        producto = productos.get(item.producto_id)
        if producto is None:
            raise _invalido(f"El producto {item.producto_id} no existe en tu tienda.")
        if not producto.activo:
            raise _invalido(f"«{producto.nombre}» está dado de baja y no se puede vender.")
        if datos.modalidad == ModalidadCompra.FIN_DE_MES and not producto.permite_fin_de_mes:
            raise _invalido(f"«{producto.nombre}» no se puede vender para pago a fin de mes.")
        if datos.modalidad == ModalidadCompra.CUOTAS and not producto.permite_cuotas:
            raise _invalido(f"«{producto.nombre}» no se puede vender en cuotas.")
        precio = convertir(producto.precio_lista, PEN, moneda)  # los precios de la tienda están en soles
        subtotal = redondear(precio * item.cantidad, DECIMALES_MONTO)
        lineas.append((producto, item.cantidad, precio, subtotal))
        monto_total += subtotal

    # --- cuotas
    if datos.modalidad == ModalidadCompra.CUOTAS:
        num_cuotas = datos.num_cuotas
        if num_cuotas > condicion.max_meses:
            raise _invalido(f"El cliente puede comprar hasta en {condicion.max_meses} cuotas; se pidieron {num_cuotas}.")
    else:
        num_cuotas = 1

    # --- ciclo: corte, pago y gracia
    fecha_corte = ciclo_credito.fecha_corte_asignada(fecha_hora.replace(tzinfo=None), condicion.dia_corte, condicion.hora_corte)
    _validar_cortes_abiertos(db, cliente.id_cliente, fecha_corte, num_cuotas if datos.modalidad == ModalidadCompra.CUOTAS else 0)
    fecha_pago_ciclo = ciclo_credito.fecha_pago_del_ciclo(fecha_corte, condicion.dia_pago)
    dias_gracia = ciclo_credito.dias_30_360(fecha_hora.date(), fecha_pago_ciclo)

    # --- motor financiero (con la tasa compensatoria pactada)
    tipo = TipoTasa(condicion.tipo_tasa_comp.value)
    if datos.modalidad == ModalidadCompra.CUOTAS:
        plan = amortizacion.calcular_plan_frances(
            capital=monto_total, tasa_pct=condicion.tasa_compensatoria, tipo=tipo, plazo_tasa_dias=condicion.plazo_tasa_comp_dias,
            capitalizacion_dias=condicion.capitaliz_comp_dias, periodo_pago_dias=PERIODO_DE_PAGO_DIAS, num_cuotas=num_cuotas, dias_gracia=dias_gracia,
        )
        tep, capital_capitalizado = plan.tep_pct, plan.capital_capitalizado
        fechas = ciclo_credito.fechas_de_cuotas(fecha_pago_ciclo, num_cuotas)
    else:
        plan = None
        tep = amortizacion.calcular_tep_pct(
            condicion.tasa_compensatoria, tipo, condicion.plazo_tasa_comp_dias, condicion.capitaliz_comp_dias, PERIODO_DE_PAGO_DIAS
        )
        capital_capitalizado = redondear(amortizacion.capitalizar_gracia(monto_total, tep, dias_gracia, PERIODO_DE_PAGO_DIAS), DECIMALES_MONTO)
        fechas = [fecha_pago_ciclo]

    return _Borrador(
        cliente=cliente, condicion=condicion, fecha_hora=fecha_hora, modalidad=datos.modalidad, lineas=lineas, monto_total=monto_total,
        fecha_corte=fecha_corte, fecha_pago_ciclo=fecha_pago_ciclo, dias_gracia=dias_gracia, tep_pct=tep, capital_capitalizado=capital_capitalizado,
        num_cuotas=num_cuotas, plan=plan, fechas_cuotas=fechas, limite=condicion.limite_credito,
        capital_pendiente=capital_pendiente(db, cliente.id_cliente, moneda),
    )


# ---------------------------------------------------------------- operaciones

def simular(db: Session, tienda_id: int, datos: CompraCrear) -> CompraRespuesta:
    """Calcula la compra completa (cronograma incluido) SIN guardarla; dice si excede el límite."""
    return _respuesta_de_borrador(_calcular(db, tienda_id, datos))


def registrar(db: Session, tienda_id: int, datos: CompraCrear, actor: UsuarioActual) -> CompraRespuesta:
    b = _calcular(db, tienda_id, datos, bloquear_cliente=True)
    simbolo = b.condicion.moneda.simbolo
    if b.excede_limite:
        raise _conflicto(
            f"La compra ({simbolo} {b.monto_total}) excede el crédito disponible ({simbolo} {b.credito_disponible}): "
            f"límite {simbolo} {b.limite}, capital pendiente {simbolo} {b.capital_pendiente}."
        )

    compra = Compra(
        cliente_id=b.cliente.id_cliente, condicion_id=b.condicion.id_condicion, fecha_hora_compra=b.fecha_hora, modalidad=b.modalidad,
        num_cuotas=b.num_cuotas, monto_total=b.monto_total, tep_aplicada=b.tep_pct, fecha_corte_asignada=b.fecha_corte,
        fecha_primer_pago=b.fecha_primer_pago, dias_gracia=b.dias_gracia, capital_capitalizado=b.capital_capitalizado, estado=EstadoCompra.VIGENTE,
    )
    db.add(compra)
    db.flush()
    for producto, cantidad, precio, subtotal in b.lineas:
        db.add(DetalleCompra(compra_id=compra.id_compra, producto_id=producto.id_producto, cantidad=cantidad, precio_unitario=precio, subtotal=subtotal))
    if b.plan is not None:
        for fila in b.plan.cronograma:
            db.add(Cuota(
                compra_id=compra.id_compra, numero_cuota=fila.numero, fecha_vencimiento=b.fechas_cuotas[fila.numero - 1],
                saldo_inicial=fila.saldo_inicial, interes=fila.interes, amortizacion=fila.amortizacion, monto_cuota=fila.cuota,
                saldo_final=fila.saldo_final, estado=EstadoCuota.PENDIENTE,
            ))
    servicio_bitacora.registrar(
        db, actor.id_usuario, EntidadBitacora.COMPRA, compra.id_compra, AccionBitacora.ALTA,
        {
            "cliente_id": b.cliente.id_cliente, "modalidad": b.modalidad.value, "moneda": b.condicion.moneda.codigo_iso,
            "monto_total": str(b.monto_total), "num_cuotas": b.num_cuotas, "fecha_corte": b.fecha_corte.isoformat(),
            "fecha_primer_pago": b.fecha_primer_pago.isoformat(), "dias_gracia": b.dias_gracia, "id_condicion": b.condicion.id_condicion,
            "items": [{"producto_id": p.id_producto, "cantidad": str(c)} for p, c, _, _ in b.lineas],
        },
    )
    db.commit()
    return obtener(db, tienda_id, compra.id_compra)


def obtener(db: Session, tienda_id: int, id_compra: int) -> CompraRespuesta:
    return _respuesta_de_compra(_compra_de_tienda(db, tienda_id, id_compra))


def listar_propias(db: Session, tienda_id: int, cliente_id: int, limite: int, desplazamiento: int) -> list[CompraRespuesta]:
    consulta = (
        select(Compra).join(Compra.cliente)
        .where(Cliente.tienda_id == tienda_id, Compra.cliente_id == cliente_id)
        .options(*_opciones_de_carga()).order_by(Compra.fecha_hora_compra.desc(), Compra.id_compra.desc())
    )
    return [_respuesta_de_compra(compra) for compra in db.scalars(consulta.limit(limite).offset(desplazamiento))]


def listar(
    db: Session,
    tienda_id: int,
    cliente_id: int | None,
    estado: EstadoCompra | None,
    modalidad: ModalidadCompra | None,
    desde: date | None,
    hasta: date | None,
    limite: int,
    desplazamiento: int,
) -> list[CompraResumen]:
    consulta = (
        select(Compra).join(Cliente, Cliente.id_cliente == Compra.cliente_id).where(Cliente.tienda_id == tienda_id)
        .options(*_opciones_de_carga()).order_by(Compra.fecha_hora_compra.desc(), Compra.id_compra.desc())
    )
    if cliente_id is not None:
        consulta = consulta.where(Compra.cliente_id == cliente_id)
    if estado is not None:
        consulta = consulta.where(Compra.estado == estado)
    if modalidad is not None:
        consulta = consulta.where(Compra.modalidad == modalidad)
    if desde is not None:
        consulta = consulta.where(Compra.fecha_hora_compra >= datetime.combine(desde, time.min, tzinfo=ZONA_LIMA))
    if hasta is not None:
        consulta = consulta.where(Compra.fecha_hora_compra < datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=ZONA_LIMA))
    resultado = []
    for c in db.scalars(consulta.limit(limite).offset(desplazamiento)):
        resultado.append(CompraResumen(
            id_compra=c.id_compra, fecha_hora_compra=c.fecha_hora_compra, cliente=_cliente_resumen(c.cliente), modalidad=c.modalidad,
            moneda=MonedaResumen(codigo_iso=c.condicion.moneda.codigo_iso, simbolo=c.condicion.moneda.simbolo), num_cuotas=c.num_cuotas,
            monto_total=c.monto_total, total_a_pagar=_total_a_pagar(c), fecha_primer_pago=c.fecha_primer_pago, estado=c.estado,
        ))
    return resultado


def anular(db: Session, tienda_id: int, id_compra: int, motivo: str, actor: UsuarioActual) -> CompraRespuesta:
    # La emisión y la anulación se excluyen sobre el mismo cliente.
    db.scalar(
        select(Cliente.id_cliente).join(Cliente.compras)
        .where(Compra.id_compra == id_compra, Cliente.tienda_id == tienda_id).with_for_update(of=Cliente)
    )
    compra = _compra_de_tienda(db, tienda_id, id_compra)
    if compra.estado != EstadoCompra.VIGENTE:
        raise _conflicto(f"La compra ya está {compra.estado.value.lower()}.")
    if db.scalar(select(EstadoCuentaDetalle.id_detalle_ec).where(EstadoCuentaDetalle.compra_id == id_compra).limit(1)) is not None:
        raise _conflicto("La compra ya figura en un estado de cuenta emitido: no se puede anular.")
    ids_cuotas = [q.id_cuota for q in compra.cuotas]
    if ids_cuotas and db.scalar(select(Pago.id_pago).where(Pago.cuota_id.in_(ids_cuotas)).limit(1)) is not None:
        raise _conflicto("La compra ya tiene pagos registrados: no se puede anular.")

    compra.estado = EstadoCompra.ANULADA
    servicio_bitacora.registrar(
        db, actor.id_usuario, EntidadBitacora.COMPRA, compra.id_compra, AccionBitacora.ANULACION,
        {"motivo": motivo, "monto_total": str(compra.monto_total)},
    )
    db.commit()
    return obtener(db, tienda_id, id_compra)

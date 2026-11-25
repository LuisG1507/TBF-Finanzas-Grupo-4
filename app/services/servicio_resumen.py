"""Consultas de cartera y cobranza. Los reportes agregados se expresan en soles."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.tiempo import ZONA_LIMA, hoy_lima
from app.models import Bitacora, Cliente, Compra, CondicionCredito, EstadoCuenta, Pago
from app.models.enumeraciones import (
    AccionBitacora, EntidadBitacora, EstadoCompra, EstadoCuentaEstado, EstadoCuota, EstadoPago, ModalidadCompra,
    TipoItemEstadoCuenta,
)
from app.schemas.schemas_resumen import (
    CierreMensual, CobranzaSemanal, CuotaDelMes, IndicadoresTablero, PosicionCliente, RespuestaTablero, ResumenMiCuenta,
)
from app.services import ciclo_credito, servicio_clientes, servicio_compras, servicio_pagos
from app.services.moneda import PEN, a_soles, convertir

CERO = Decimal("0.00")
UN_DIA = timedelta(days=1)


@dataclass(frozen=True)
class Vencimiento:
    fecha: date
    capital: Decimal
    programado: Decimal
    moneda: str
    compra: Compra
    fecha_cobro: date | None
    cuota_id: int | None = None
    estado_cuota: EstadoCuota | None = None


def _consultar_clientes(db: Session, tienda_id: int, cliente_id: int | None = None) -> list[Cliente]:
    compras = selectinload(Cliente.compras)
    consulta = select(Cliente).where(Cliente.tienda_id == tienda_id).options(
        selectinload(Cliente.tienda),
        selectinload(Cliente.condiciones_credito).selectinload(CondicionCredito.moneda),
        compras.selectinload(Compra.cuotas),
        compras.selectinload(Compra.condicion).selectinload(CondicionCredito.moneda),
        selectinload(Cliente.estados_cuenta).selectinload(EstadoCuenta.detalles),
        selectinload(Cliente.pagos),
    ).order_by(Cliente.id_cliente)
    if cliente_id is not None:
        consulta = consulta.where(Cliente.id_cliente == cliente_id)
    return list(db.scalars(consulta))


def _fecha_local(fecha: datetime) -> date:
    return fecha.astimezone(ZONA_LIMA).date()


def _fecha_cobro(pago: Pago) -> date:
    # El registro anterior al bloque A guardaba la fecha histórica a medianoche UTC.
    utc = pago.fecha_hora_pago.astimezone(timezone.utc)
    return utc.date() if utc.time() == time.min else _fecha_local(utc)


def _condicion_pactada(cliente: Cliente, fecha: date) -> CondicionCredito | None:
    return max(
        (c for c in cliente.condiciones_credito if c.vigente_desde <= fecha),
        key=lambda c: (c.vigente_desde, c.id_condicion), default=None,
    )


def _interes_al_corte(estado: EstadoCuenta, ajuste_anterior: Decimal) -> Decimal:
    ajustes = [
        d.monto for d in estado.detalles
        if d.tipo_item == TipoItemEstadoCuenta.INT_COMPENSATORIO and d.compra_id is None and d.cuota_id is None
        and d.dias_transcurridos and d.fecha_referencia and d.fecha_referencia > estado.fecha_pago
    ]
    return estado.total_interes_comp - (sum(ajustes, CERO) if ajustes else ajuste_anterior)


class CarteraCliente:
    def __init__(
        self, cliente: Cliente, anulaciones: dict[int, date], movimientos: list[tuple[date, bool]], ajustes: dict[int, Decimal],
    ):
        self.cliente = cliente
        self.movimientos = movimientos
        self.anulaciones = anulaciones
        self.compras = {c.id_compra: c for c in cliente.compras}
        self.compras_por_cuota = {q.id_cuota: c for c in cliente.compras for q in c.cuotas}
        self.pagos = [p for p in cliente.pagos if p.estado == EstadoPago.REGISTRADO]
        self.estados = {e.id_estado_cuenta: e for e in cliente.estados_cuenta}
        self.pagos_por_estado = {p.estado_cuenta_id: p for p in self.pagos if p.estado_cuenta_id in self.estados}
        self.ajustes = ajustes
        self.cuotas_facturadas = {d.cuota_id for e in cliente.estados_cuenta for d in e.detalles if d.cuota_id is not None}
        self.compras_facturadas = {
            d.compra_id for e in cliente.estados_cuenta for d in e.detalles if d.tipo_item == TipoItemEstadoCuenta.COMPRA
        }
        self.vencimientos = self._vencimientos()

    def _vencimientos(self) -> list[Vencimiento]:
        fechas_cuotas = {p.cuota_id: _fecha_cobro(p) for p in self.pagos if p.cuota_id is not None}
        fechas_compras = {}
        for id_estado, pago in self.pagos_por_estado.items():
            fecha = _fecha_cobro(pago)
            for d in self.estados[id_estado].detalles:
                if d.cuota_id is not None:
                    fechas_cuotas[d.cuota_id] = fecha
                elif d.compra_id is not None:
                    fechas_compras[d.compra_id] = fecha
        vencimientos = []
        for c in self.compras.values():
            moneda = c.condicion.moneda.codigo_iso
            if c.modalidad == ModalidadCompra.FIN_DE_MES:
                vencimientos.append(Vencimiento(c.fecha_primer_pago, c.monto_total, c.capital_capitalizado, moneda, c,
                                                fechas_compras.get(c.id_compra)))
            else:
                vencimientos.extend(Vencimiento(q.fecha_vencimiento, q.amortizacion, q.monto_cuota, moneda, c,
                                                fechas_cuotas.get(q.id_cuota), q.id_cuota, q.estado) for q in c.cuotas)
        return vencimientos

    def moneda_estado(self, estado: EstadoCuenta) -> str:
        for detalle in estado.detalles:
            compra = self.compras.get(detalle.compra_id) or self.compras_por_cuota.get(detalle.cuota_id)
            if compra is not None:
                return compra.condicion.moneda.codigo_iso
        condicion = _condicion_pactada(self.cliente, estado.fecha_pago)
        return condicion.moneda.codigo_iso if condicion is not None else PEN

    def cobros_en_soles(self):
        for pago in self.pagos:
            fecha = _fecha_cobro(pago)
            estado = self.estados.get(pago.estado_cuenta_id)
            if estado is not None:
                moneda = self.moneda_estado(estado)
            elif pago.cuota_id in self.compras_por_cuota:
                moneda = self.compras_por_cuota[pago.cuota_id].condicion.moneda.codigo_iso
            else:
                condicion = _condicion_pactada(self.cliente, fecha)
                moneda = condicion.moneda.codigo_iso if condicion else PEN
            yield fecha, a_soles(pago.monto_pagado, moneda)

    def activa_en(self, fecha: date, hoy: date) -> bool:
        if fecha == hoy:
            return self.cliente.activo
        if _fecha_local(self.cliente.fecha_registro) > fecha:
            return False
        return next((activo for dia, activo in reversed(self.movimientos) if dia <= fecha), True)

    def vigente_en(self, compra: Compra, fecha: date) -> bool:
        anulada = self.anulaciones.get(compra.id_compra)
        if compra.estado == EstadoCompra.ANULADA and (anulada is None or fecha >= anulada):
            return False
        return _fecha_local(compra.fecha_hora_compra) <= fecha

    def saldo_historico(self, fecha: date, moneda: str) -> Decimal:
        return sum((
            convertir(v.capital, v.moneda, moneda) for v in self.vencimientos
            if self.vigente_en(v.compra, fecha)
            and (v.fecha_cobro > fecha if v.fecha_cobro is not None else
                 v.estado_cuota != EstadoCuota.PAGADA and v.compra.estado != EstadoCompra.CANCELADA)
        ), CERO)

    def mora_en(self, fecha: date):
        for estado in self.estados.values():
            if estado.fecha_pago >= fecha:
                continue
            pago = self.pagos_por_estado.get(estado.id_estado_cuenta)
            pagado = _fecha_cobro(pago) <= fecha if pago is not None else estado.estado == EstadoCuentaEstado.PAGADO
            if pagado:
                continue
            condicion = _condicion_pactada(self.cliente, estado.fecha_pago)
            if condicion is not None:
                ajuste = self.ajustes.get(pago.id_pago, CERO) if pago is not None else CERO
                yield estado, servicio_pagos.liquidar_estado(
                    estado, condicion, fecha, interes_del_corte=_interes_al_corte(estado, ajuste),
                )

    def posicion(self, hoy: date, cierres: list[date]) -> PosicionCliente:
        condicion = servicio_clientes.condicion_vigente(self.cliente)
        moneda = condicion.moneda.codigo_iso if condicion is not None else PEN
        vencidos = list(self.mora_en(hoy))
        dias_atraso = max((r.dias_mora for _, r in vencidos), default=0)
        mora = sum((convertir(r.interes_mora, self.moneda_estado(e), moneda) for e, r in vencidos), CERO)
        proximos = defaultdict(lambda: CERO)
        for e, r in vencidos:
            proximos[e.fecha_pago] += convertir(r.total_exigible, self.moneda_estado(e), moneda)
        for e in self.estados.values():
            if e.estado != EstadoCuentaEstado.PAGADO and e.fecha_pago >= hoy:
                proximos[e.fecha_pago] += convertir(e.total_pagar, self.moneda_estado(e), moneda)
        for v in self.vencimientos:
            facturado = v.cuota_id in self.cuotas_facturadas if v.cuota_id else v.compra.id_compra in self.compras_facturadas
            if not facturado and v.fecha >= hoy and v.compra.estado == EstadoCompra.VIGENTE and v.estado_cuota != EstadoCuota.PAGADA:
                proximos[v.fecha] += convertir(v.programado, v.moneda, moneda)
        proximo = min(proximos, default=None)
        situacion = "AL_DIA"
        if vencidos or any(e.fecha_pago < hoy and e.estado != EstadoCuentaEstado.PAGADO for e in self.estados.values()):
            situacion = "EN_MORA"
        elif proximo is not None and proximo <= hoy + timedelta(days=7):
            situacion = "POR_VENCER"
        return PosicionCliente(
            cliente_id=self.cliente.id_cliente, moneda=moneda,
            saldo_capital=servicio_compras.sumar_capital_pendiente(self.compras.values(), moneda),
            mora_acumulada=mora, dias_atraso=dias_atraso, situacion=situacion, proximo_vencimiento=proximo,
            monto_proximo_pago=proximos[proximo] if proximo is not None else None,
            saldos_cierre_previos=[self.saldo_historico(c, moneda) for c in cierres],
        )


def _carteras(db: Session, tienda_id: int, cliente_id: int | None = None) -> list[CarteraCliente]:
    clientes = _consultar_clientes(db, tienda_id, cliente_id)
    ids_clientes = [c.id_cliente for c in clientes]
    ids_compras = [c.id_compra for cliente in clientes for c in cliente.compras if c.estado == EstadoCompra.ANULADA]
    ids_pagos = [p.id_pago for cliente in clientes for p in cliente.pagos if p.estado == EstadoPago.REGISTRADO]
    anulaciones = {}
    movimientos = defaultdict(list)
    ajustes = {}
    consulta = select(Bitacora).where(
        ((Bitacora.entidad == EntidadBitacora.COMPRA) & (Bitacora.entidad_id.in_(ids_compras)) &
         (Bitacora.accion == AccionBitacora.ANULACION)) |
        ((Bitacora.entidad == EntidadBitacora.CLIENTE) & (Bitacora.entidad_id.in_(ids_clientes)) &
         (Bitacora.accion.in_([AccionBitacora.BAJA, AccionBitacora.MODIFICACION]))) |
        ((Bitacora.entidad == EntidadBitacora.PAGO) & (Bitacora.entidad_id.in_(ids_pagos)) &
         (Bitacora.accion == AccionBitacora.ALTA))
    ).order_by(Bitacora.fecha_hora, Bitacora.id_bitacora)
    for fila in db.scalars(consulta):
        fecha = _fecha_local(fila.fecha_hora)
        if fila.entidad == EntidadBitacora.COMPRA:
            anulaciones[fila.entidad_id] = fecha
        elif fila.entidad == EntidadBitacora.PAGO:
            if fila.detalle and "interes_comp_atraso" in fila.detalle:
                ajustes[fila.entidad_id] = Decimal(fila.detalle["interes_comp_atraso"])
        elif fila.accion == AccionBitacora.BAJA:
            movimientos[fila.entidad_id].append((fecha, False))
        elif fila.detalle and fila.detalle.get("activo") is True:
            movimientos[fila.entidad_id].append((fecha, True))
    return [CarteraCliente(c, anulaciones, movimientos[c.id_cliente], ajustes) for c in clientes]


def _meses_de_cierre(hoy: date) -> list[date]:
    return [ciclo_credito.sumar_meses(hoy.replace(day=1), -n) for n in range(5, 0, -1)]


def _estado_cuota(v: Vencimiento, hoy: date) -> EstadoCuota:
    if v.estado_cuota == EstadoCuota.PAGADA:
        return EstadoCuota.PAGADA
    return EstadoCuota.VENCIDA if v.fecha < hoy else (v.estado_cuota or EstadoCuota.PENDIENTE)


def tablero(db: Session, tienda_id: int) -> RespuestaTablero:
    hoy = hoy_lima()
    carteras = _carteras(db, tienda_id)
    meses = _meses_de_cierre(hoy)
    cierres = [ciclo_credito.sumar_meses(mes, 1) - UN_DIA for mes in meses]
    posiciones = [c.posicion(hoy, cierres) for c in carteras]
    inicio_mes = hoy.replace(day=1)
    fin_mes = ciclo_credito.sumar_meses(inicio_mes, 1) - UN_DIA
    cuotas = sorted((
        CuotaDelMes(cliente_id=v.compra.cliente_id, fecha_vencimiento=v.fecha, monto=a_soles(v.programado, v.moneda),
                   estado=_estado_cuota(v, hoy))
        for c in carteras for v in c.vencimientos
        if v.cuota_id is not None and inicio_mes <= v.fecha <= fin_mes and c.vigente_en(v.compra, hoy)
    ), key=lambda q: (q.fecha_vencimiento, q.cliente_id))

    semana = hoy - timedelta(days=hoy.weekday())
    cobranza = []
    cobros = [cobro for c in carteras for cobro in c.cobros_en_soles()]
    for n in range(7, -1, -1):
        desde = semana - timedelta(weeks=n)
        hasta = desde + timedelta(days=6)
        programado = sum((a_soles(v.programado, v.moneda) for c in carteras for v in c.vencimientos
                          if desde <= v.fecha <= hasta and c.vigente_en(v.compra, min(hoy, hasta))), CERO)
        cobrado = sum((monto for fecha, monto in cobros if desde <= fecha <= min(hasta, hoy)), CERO)
        cobranza.append(CobranzaSemanal(desde=desde, hasta=hasta, programado=programado, cobrado=cobrado))

    cierres_mensuales = [CierreMensual(
        mes=mes,
        cuotas_programadas=sum((a_soles(v.programado, v.moneda) for c in carteras for v in c.vencimientos
                                if v.cuota_id is not None and mes <= v.fecha <= cierre and c.vigente_en(v.compra, cierre)), CERO),
        mora_acumulada=sum((a_soles(r.interes_mora, c.moneda_estado(e)) for c in carteras for e, r in c.mora_en(cierre)), CERO),
        clientes_activos=sum(c.activa_en(cierre, hoy) for c in carteras),
    ) for mes, cierre in zip(meses, cierres)]
    return RespuestaTablero(
        hoy=hoy, posiciones=posiciones, cobranza_semanal=cobranza, cuotas_del_mes=cuotas, cierres_mensuales=cierres_mensuales,
        kpis=IndicadoresTablero(
            saldo_por_cobrar=sum((a_soles(p.saldo_capital, p.moneda) for p in posiciones), CERO),
            cuotas_del_mes=sum((q.monto for q in cuotas), CERO),
            mora_acumulada=sum((a_soles(p.mora_acumulada, p.moneda) for p in posiciones), CERO),
            clientes_activos=sum(c.cliente.activo for c in carteras),
        ),
    )


def mi_cuenta(db: Session, tienda_id: int, cliente_id: int) -> ResumenMiCuenta:
    carteras = _carteras(db, tienda_id, cliente_id)
    if not carteras:
        raise HTTPException(404, "El cliente no existe.")
    cartera = carteras[0]
    hoy = hoy_lima()
    cierres = [ciclo_credito.sumar_meses(mes, 1) - UN_DIA for mes in _meses_de_cierre(hoy)]
    posicion = cartera.posicion(hoy, cierres)
    cliente = servicio_clientes.mi_perfil(db, tienda_id, cliente_id)
    condicion = cliente.condicion
    return ResumenMiCuenta(
        hoy=hoy, tienda=cartera.cliente.tienda.nombre_comercial, posicion=posicion, condicion=condicion,
        credito_disponible=max(condicion.limite_credito - posicion.saldo_capital, CERO) if condicion is not None else None,
    )

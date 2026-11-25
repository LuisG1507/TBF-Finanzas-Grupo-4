"""Emite estados de cuenta al corte y conserva los importes de las compras pactadas."""
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.tiempo import ZONA_LIMA, ahora_lima, hoy_lima
from app.models.cliente import Cliente, CondicionCredito
from app.models.compra import Compra, Cuota
from app.models.enumeraciones import (
    AccionBitacora,
    EntidadBitacora,
    EstadoCompra,
    EstadoCuentaEstado,
    EstadoCuota,
    ModalidadCompra,
    TipoItemEstadoCuenta,
)
from app.models.estado_cuenta import EstadoCuenta, EstadoCuentaDetalle
from app.schemas.schemas_clientes import MonedaResumen
from app.schemas.schemas_estados_cuenta import EstadoCuentaDetalleRespuesta, EstadoCuentaRespuesta, EstadoCuentaResumen
from app.services import ciclo_credito, servicio_bitacora
from app.services.servicio_compras import PERIODO_DE_PAGO_DIAS

CERO = Decimal("0.00")
CONCEPTOS = {
    TipoItemEstadoCuenta.COMPRA: "Compra a fin de mes",
    TipoItemEstadoCuenta.CUOTA: "Cuota",
    TipoItemEstadoCuenta.INT_COMPENSATORIO: "Intereses compensatorios",
    TipoItemEstadoCuenta.INT_MORATORIO: "Intereses por mora",
}


def _consulta(tienda_id: int):
    detalles = selectinload(EstadoCuenta.detalles)
    return (
        select(EstadoCuenta).join(EstadoCuenta.cliente).where(Cliente.tienda_id == tienda_id)
        .options(
            selectinload(EstadoCuenta.cliente),
            detalles.selectinload(EstadoCuentaDetalle.compra).selectinload(Compra.condicion).selectinload(CondicionCredito.moneda),
            detalles.selectinload(EstadoCuentaDetalle.cuota).selectinload(Cuota.compra)
            .selectinload(Compra.condicion).selectinload(CondicionCredito.moneda),
        )
    )


def _compra_del_detalle(detalle: EstadoCuentaDetalle) -> Compra | None:
    return detalle.compra or (detalle.cuota.compra if detalle.cuota is not None else None)


def _resumen(estado: EstadoCuenta, hoy: date) -> EstadoCuentaResumen:
    compra = next((compra for d in estado.detalles if (compra := _compra_del_detalle(d)) is not None), None)
    moneda = compra.condicion.moneda if compra is not None else None
    estado_visible = estado.estado
    if estado_visible != EstadoCuentaEstado.PAGADO and estado.fecha_pago < hoy:
        estado_visible = EstadoCuentaEstado.VENCIDO
    return EstadoCuentaResumen(
        id_estado_cuenta=estado.id_estado_cuenta,
        cliente_id=estado.cliente_id,
        cliente_nombre=f"{estado.cliente.nombres} {estado.cliente.apellidos}",
        moneda=MonedaResumen(codigo_iso=moneda.codigo_iso, simbolo=moneda.simbolo) if moneda is not None else None,
        anio=estado.anio,
        mes=estado.mes,
        fecha_corte=estado.fecha_corte,
        fecha_pago=estado.fecha_pago,
        total_capital=estado.total_capital,
        total_interes_comp=estado.total_interes_comp,
        total_interes_mora=estado.total_interes_mora,
        total_pagar=estado.total_pagar,
        estado=estado_visible,
        fecha_generacion=estado.fecha_generacion,
    )


def _detalle(detalle: EstadoCuentaDetalle) -> EstadoCuentaDetalleRespuesta:
    compra, cuota = _compra_del_detalle(detalle), detalle.cuota
    return EstadoCuentaDetalleRespuesta(
        id_detalle_ec=detalle.id_detalle_ec,
        compra_id=compra.id_compra if compra is not None else None,
        cuota_id=detalle.cuota_id,
        tipo_item=detalle.tipo_item,
        concepto=CONCEPTOS[detalle.tipo_item],
        fecha_referencia=detalle.fecha_referencia,
        fecha_hora_compra=compra.fecha_hora_compra.astimezone(ZONA_LIMA) if compra is not None else None,
        dias_transcurridos=detalle.dias_transcurridos,
        tasa_aplicada=detalle.tasa_aplicada,
        monto=detalle.monto,
        orden=detalle.orden,
        numero_cuota=cuota.numero_cuota if cuota is not None else None,
        amortizacion=cuota.amortizacion if cuota is not None else None,
        interes_cuota=cuota.interes if cuota is not None else None,
    )


def obtener(db: Session, tienda_id: int, id_estado: int, cliente_id: int | None = None) -> EstadoCuentaRespuesta:
    consulta = _consulta(tienda_id).where(EstadoCuenta.id_estado_cuenta == id_estado)
    if cliente_id is not None:
        consulta = consulta.where(EstadoCuenta.cliente_id == cliente_id)
    estado = db.scalar(consulta)
    if estado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El estado de cuenta no existe.")
    return EstadoCuentaRespuesta(**_resumen(estado, hoy_lima()).model_dump(), detalles=[_detalle(d) for d in estado.detalles])


def listar(
    db: Session,
    tienda_id: int,
    cliente_id: int | None,
    anio: int | None,
    mes: int | None,
    estado: EstadoCuentaEstado | None,
    limite: int,
    desplazamiento: int,
) -> list[EstadoCuentaResumen]:
    hoy = hoy_lima()
    consulta = _consulta(tienda_id).order_by(EstadoCuenta.fecha_corte.desc(), EstadoCuenta.id_estado_cuenta.desc())
    if cliente_id is not None:
        consulta = consulta.where(EstadoCuenta.cliente_id == cliente_id)
    if anio is not None:
        consulta = consulta.where(EstadoCuenta.anio == anio)
    if mes is not None:
        consulta = consulta.where(EstadoCuenta.mes == mes)
    if estado == EstadoCuentaEstado.VENCIDO:
        consulta = consulta.where(or_(
            EstadoCuenta.estado == EstadoCuentaEstado.VENCIDO,
            and_(EstadoCuenta.estado == EstadoCuentaEstado.EMITIDO, EstadoCuenta.fecha_pago < hoy),
        ))
    elif estado == EstadoCuentaEstado.EMITIDO:
        consulta = consulta.where(EstadoCuenta.estado == estado, EstadoCuenta.fecha_pago >= hoy)
    elif estado is not None:
        consulta = consulta.where(EstadoCuenta.estado == estado)
    return [_resumen(e, hoy) for e in db.scalars(consulta.limit(limite).offset(desplazamiento))]


def _obligaciones_del_mes(db: Session, clientes: list[int], inicio: date, fin: date):
    """Una cuota puede pagar el mes siguiente al corte. Se verifica su corte exacto al agrupar."""
    return db.execute(
        select(Compra, Cuota)
        .outerjoin(Compra.cuotas.and_(
            Cuota.estado == EstadoCuota.PENDIENTE,
            Cuota.fecha_vencimiento >= inicio,
            Cuota.fecha_vencimiento < ciclo_credito.sumar_meses(fin, 1),
        ))
        .where(Compra.cliente_id.in_(clientes), Compra.estado == EstadoCompra.VIGENTE)
        .where(or_(
            and_(Compra.modalidad == ModalidadCompra.FIN_DE_MES, Compra.fecha_corte_asignada >= inicio, Compra.fecha_corte_asignada < fin),
            and_(Compra.modalidad == ModalidadCompra.CUOTAS, Cuota.id_cuota.is_not(None)),
        ))
        .options(selectinload(Compra.condicion))
        .order_by(Compra.fecha_hora_compra, Compra.id_compra, Cuota.numero_cuota)
    )


def _guardar_estado(
    db: Session, cliente_id: int, corte: date, pago: date, obligaciones: list[tuple[Compra, Cuota | None]], usuario_id: int
) -> None:
    if len({compra.condicion.moneda_id for compra, _ in obligaciones}) > 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"El corte del {corte.isoformat()} del cliente {cliente_id} contiene obligaciones en monedas distintas.",
        )
    estado = EstadoCuenta(
        cliente_id=cliente_id, anio=corte.year, mes=corte.month, fecha_corte=corte, fecha_pago=pago,
        total_capital=CERO, total_interes_comp=CERO, total_interes_mora=CERO, estado=EstadoCuentaEstado.EMITIDO,
    )
    for compra, cuota in obligaciones:
        orden = len(estado.detalles) + 1
        if cuota is None:
            fecha_compra = compra.fecha_hora_compra.astimezone(ZONA_LIMA).date()
            interes = compra.capital_capitalizado - compra.monto_total
            estado.detalles.extend([
                EstadoCuentaDetalle(
                    compra_id=compra.id_compra, tipo_item=TipoItemEstadoCuenta.COMPRA,
                    fecha_referencia=fecha_compra, monto=compra.monto_total, orden=orden,
                ),
                EstadoCuentaDetalle(
                    compra_id=compra.id_compra, tipo_item=TipoItemEstadoCuenta.INT_COMPENSATORIO,
                    fecha_referencia=fecha_compra, dias_transcurridos=compra.dias_gracia,
                    tasa_aplicada=compra.tep_aplicada, monto=interes, orden=orden + 1,
                ),
            ])
            estado.total_capital += compra.monto_total
            estado.total_interes_comp += interes
        else:
            estado.detalles.append(EstadoCuentaDetalle(
                compra_id=compra.id_compra, cuota_id=cuota.id_cuota, tipo_item=TipoItemEstadoCuenta.CUOTA,
                fecha_referencia=cuota.fecha_vencimiento, dias_transcurridos=PERIODO_DE_PAGO_DIAS,
                tasa_aplicada=compra.tep_aplicada, monto=cuota.monto_cuota, orden=orden,
            ))
            estado.total_capital += cuota.amortizacion
            estado.total_interes_comp += cuota.interes
            cuota.estado = EstadoCuota.FACTURADA

    estado.total_pagar = estado.total_capital + estado.total_interes_comp
    db.add(estado)
    db.flush()
    servicio_bitacora.registrar(
        db, usuario_id, EntidadBitacora.ESTADO_CUENTA, estado.id_estado_cuenta, AccionBitacora.ALTA,
        {"cliente_id": cliente_id, "fecha_corte": corte.isoformat(), "fecha_pago": pago.isoformat(),
         "total_pagar": str(estado.total_pagar), "cantidad_items": len(estado.detalles)},
    )


def generar(db: Session, tienda_id: int, usuario_id: int, anio: int, mes: int) -> list[EstadoCuentaResumen]:
    inicio = date(anio, mes, 1)
    ahora = ahora_lima()
    if inicio > ahora.date():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El mes del corte no puede ser futuro.")
    fin = ciclo_credito.sumar_meses(inicio, 1)

    # Todos los emisores toman los bloqueos en el mismo orden antes de consultar qué cortes existen.
    consulta_clientes = (
        select(Cliente.id_cliente).where(Cliente.tienda_id == tienda_id, Cliente.activo.is_(True))
        .order_by(Cliente.id_cliente).with_for_update()
    )
    clientes = list(db.scalars(consulta_clientes))
    consulta_mes = _consulta(tienda_id).where(EstadoCuenta.anio == anio, EstadoCuenta.mes == mes)
    existentes = set(db.execute(
        select(EstadoCuenta.cliente_id, EstadoCuenta.fecha_corte, EstadoCuenta.fecha_pago)
        .join(EstadoCuenta.cliente).where(Cliente.tienda_id == tienda_id, EstadoCuenta.anio == anio, EstadoCuenta.mes == mes)
    ).tuples())

    grupos: dict[tuple[int, date, date], list[tuple[Compra, Cuota | None]]] = defaultdict(list)
    for compra, cuota in _obligaciones_del_mes(db, clientes, inicio, fin):
        corte, pago = compra.fecha_corte_asignada, compra.fecha_primer_pago
        if cuota is not None:
            corte = ciclo_credito.sumar_meses(corte, cuota.numero_cuota)
            pago = cuota.fecha_vencimiento
        if inicio <= corte < fin:
            grupos[compra.cliente_id, corte, pago].append((compra, cuota))

    for clave, obligaciones in grupos.items():
        cliente_id, corte, pago = clave
        hora_corte = max(compra.condicion.hora_corte for compra, _ in obligaciones)
        if clave not in existentes and datetime.combine(corte, hora_corte, ZONA_LIMA) <= ahora:
            _guardar_estado(db, cliente_id, corte, pago, obligaciones, usuario_id)

    db.commit()
    ordenados = consulta_mes.order_by(EstadoCuenta.fecha_corte, EstadoCuenta.cliente_id, EstadoCuenta.fecha_pago)
    return [_resumen(e, ahora.date()) for e in db.scalars(ordenados)]

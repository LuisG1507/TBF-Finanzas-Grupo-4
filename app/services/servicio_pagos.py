from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bitacora, CondicionCredito, Cuota, EstadoCuenta, Pago, Usuario
from app.models.enumeraciones import (
    AccionBitacora,
    EntidadBitacora,
    EstadoCompra,
    EstadoCuentaEstado,
    EstadoCuota,
    ModalidadCompra,
)
from app.services.finance import finance_pagos as pagos
from app.services.finance.finance_tasas import TipoTasa

CERO = Decimal(0)


class ErrorPago(Exception):
    """Error de negocio al registrar un pago; codigo es el estado HTTP que le corresponde."""

    def __init__(self, codigo: int, detalle: str | dict):
        self.codigo = codigo
        self.detalle = detalle


def _condicion_vigente(sesion: Session, cliente_id: int, fecha: date) -> CondicionCredito:
    """Condicion de credito del cliente vigente en la fecha de vencimiento (la mas reciente)."""
    condicion = sesion.scalars(
        select(CondicionCredito)
        .where(CondicionCredito.cliente_id == cliente_id, CondicionCredito.vigente_desde <= fecha)
        .order_by(CondicionCredito.vigente_desde.desc())
    ).first()
    if condicion is None:
        raise ErrorPago(409, "El cliente no tiene una condicion de credito vigente")
    return condicion


def calcular_exigible(sesion: Session, id_estado_cuenta: int, fecha_pago: date, monto: Decimal | None = None):
    """Deuda exigible del estado de cuenta a la fecha de pago. Sin monto, se asume el pago exacto."""
    estado = sesion.get(EstadoCuenta, id_estado_cuenta)
    if estado is None:
        raise ErrorPago(404, "El estado de cuenta no existe")
    condicion = _condicion_vigente(sesion, estado.cliente_id, estado.fecha_pago)
    tipo = TipoTasa(condicion.tipo_tasa_mora.value)

    def procesar(monto_pagado: Decimal):
        return pagos.procesar_pago(
            capital=estado.total_capital,
            interes_comp=estado.total_interes_comp,
            portes=CERO,
            seguro=CERO,
            fecha_vencimiento=estado.fecha_pago,
            fecha_pago=fecha_pago,
            monto_pagado=monto_pagado,
            tasa_mora_pct=condicion.tasa_moratoria,
            tipo_mora=tipo,
            plazo_mora_dias=condicion.plazo_tasa_mora_dias,
            capitalizacion_mora_dias=condicion.capitaliz_mora_dias if tipo == TipoTasa.NOMINAL else None,
        )

    if monto is None:
        monto = procesar(Decimal("0.01")).total_exigible
    return estado, procesar(monto)


def registrar_pago(sesion: Session, id_estado_cuenta: int, usuario_id: int, monto_pagado: Decimal, fecha_pago: date):
    """Registra la cancelacion completa de un estado de cuenta: mora -> interes compensatorio -> capital.
    Rechaza pagos parciales y devuelve el excedente; no adelanta cuotas futuras."""
    estado, resultado = calcular_exigible(sesion, id_estado_cuenta, fecha_pago, monto_pagado)
    if estado.estado == EstadoCuentaEstado.PAGADO:
        raise ErrorPago(409, "El estado de cuenta ya fue pagado")
    if sesion.get(Usuario, usuario_id) is None:
        raise ErrorPago(404, "El usuario que registra el pago no existe")
    if not resultado.aceptado:
        raise ErrorPago(400, {
            "mensaje": "Pago rechazado: no se aceptan pagos parciales",
            "total_exigible": str(resultado.total_exigible),
            "monto_recibido": str(monto_pagado),
            "faltante": str(resultado.total_exigible - monto_pagado),
        })

    ahora = datetime.now(timezone.utc)
    pago = Pago(
        cliente_id=estado.cliente_id,
        usuario_id=usuario_id,
        estado_cuenta_id=estado.id_estado_cuenta,
        fecha_hora_pago=ahora if fecha_pago == ahora.date() else datetime.combine(fecha_pago, time(0, 0), tzinfo=timezone.utc),
        monto_pagado=resultado.monto_aplicado,  # solo lo aplicado a la deuda; el excedente se devuelve
        monto_mora_aplicado=resultado.aplicado_mora,
        monto_interes_comp_aplicado=resultado.aplicado_interes_comp,
        monto_capital_aplicado=resultado.aplicado_capital,
    )
    sesion.add(pago)

    estado.total_interes_mora = resultado.interes_mora
    estado.total_pagar = resultado.total_exigible
    estado.estado = EstadoCuentaEstado.PAGADO
    for detalle in estado.detalles:
        if detalle.cuota is not None:
            detalle.cuota.estado = EstadoCuota.PAGADA
            compra = detalle.cuota.compra
            sesion.flush()
            pendiente = sesion.scalars(
                select(Cuota).where(Cuota.compra_id == compra.id_compra, Cuota.estado != EstadoCuota.PAGADA)
            ).first()
            if pendiente is None:
                compra.estado = EstadoCompra.CANCELADA
        elif detalle.compra is not None and detalle.compra.modalidad == ModalidadCompra.FIN_DE_MES:
            detalle.compra.estado = EstadoCompra.CANCELADA

    sesion.flush()
    sesion.add(Bitacora(
        usuario_id=usuario_id,
        entidad=EntidadBitacora.PAGO,
        entidad_id=pago.id_pago,
        accion=AccionBitacora.ALTA,
        detalle={
            "estado_cuenta_id": estado.id_estado_cuenta,
            "monto_recibido": str(monto_pagado),
            "monto_aplicado": str(resultado.monto_aplicado),
            "mora": str(resultado.aplicado_mora),
            "interes_comp": str(resultado.aplicado_interes_comp),
            "capital": str(resultado.aplicado_capital),
            "excedente_devuelto": str(resultado.excedente_devuelto),
            "dias_mora": resultado.dias_mora,
        },
    ))
    sesion.commit()
    sesion.refresh(pago)
    return estado, pago, resultado

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.sesion import obtener_sesion
from app.schemas import schemas_pagos as esquemas
from app.services import servicio_pagos as servicio

router = APIRouter(prefix="/pagos", tags=["Pagos"])


def _exigible(estado, resultado, fecha_pago: date) -> dict:
    return dict(
        id_estado_cuenta=estado.id_estado_cuenta,
        cliente_id=estado.cliente_id,
        fecha_vencimiento=estado.fecha_pago,
        fecha_pago=fecha_pago,
        dias_mora=resultado.dias_mora,
        tasa_mora_pct=resultado.tasa_mora_pct,
        capital=estado.total_capital,
        interes_comp=estado.total_interes_comp,
        interes_mora=resultado.interes_mora,
        total_exigible=resultado.total_exigible,
    )


@router.get("/estados-cuenta/{id_estado_cuenta}/exigible", response_model=esquemas.RespuestaExigible,
            summary="Total exigible de un estado de cuenta a una fecha de pago (incluye mora)")
def consultar_exigible(id_estado_cuenta: int, fecha_pago: date | None = None, sesion: Session = Depends(obtener_sesion)):
    fecha = fecha_pago or date.today()
    try:
        estado, resultado = servicio.calcular_exigible(sesion, id_estado_cuenta, fecha)
    except servicio.ErrorPago as error:
        raise HTTPException(status_code=error.codigo, detail=error.detalle)
    return esquemas.RespuestaExigible(**_exigible(estado, resultado, fecha))


@router.post("/estados-cuenta/{id_estado_cuenta}", response_model=esquemas.RespuestaRegistrarPago, status_code=201,
             summary="Registrar pago: mora, interes compensatorio y capital; rechaza parciales y devuelve el excedente")
def registrar_pago(id_estado_cuenta: int, datos: esquemas.EntradaRegistrarPago, sesion: Session = Depends(obtener_sesion)):
    fecha = datos.fecha_pago or date.today()
    try:
        estado, pago, resultado = servicio.registrar_pago(sesion, id_estado_cuenta, datos.usuario_id, datos.monto_pagado, fecha)
    except servicio.ErrorPago as error:
        sesion.rollback()
        raise HTTPException(status_code=error.codigo, detail=error.detalle)
    return esquemas.RespuestaRegistrarPago(
        **_exigible(estado, resultado, fecha),
        id_pago=pago.id_pago,
        fecha_hora_pago=pago.fecha_hora_pago,
        monto_recibido=datos.monto_pagado,
        monto_aplicado=resultado.monto_aplicado,
        aplicado_mora=resultado.aplicado_mora,
        aplicado_interes_comp=resultado.aplicado_interes_comp,
        aplicado_capital=resultado.aplicado_capital,
        excedente_devuelto=resultado.excedente_devuelto,
        estado_cuenta=estado.estado.value,
    )

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class EntradaRegistrarPago(BaseModel):
    usuario_id: int = Field(gt=0, description="Usuario (administrador del negocio) que registra el pago")
    monto_pagado: Decimal = Field(gt=0, decimal_places=2, examples=["916.17"])
    fecha_pago: date | None = Field(default=None, examples=["2026-10-31"], description="Fecha real del pago; por defecto, hoy")


class RespuestaExigible(BaseModel):
    id_estado_cuenta: int
    cliente_id: int
    fecha_vencimiento: date
    fecha_pago: date
    dias_mora: int
    tasa_mora_pct: Decimal
    capital: Decimal
    interes_comp: Decimal
    interes_mora: Decimal
    total_exigible: Decimal


class RespuestaRegistrarPago(RespuestaExigible):
    id_pago: int
    fecha_hora_pago: datetime
    monto_recibido: Decimal
    monto_aplicado: Decimal
    aplicado_mora: Decimal
    aplicado_interes_comp: Decimal
    aplicado_capital: Decimal
    excedente_devuelto: Decimal
    estado_cuenta: str

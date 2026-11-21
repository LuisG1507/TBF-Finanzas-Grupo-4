"""Conversión entre soles (PEN) y dólares (USD) con un tipo de cambio fijo.

Solo sirve para consolidar totales (dashboard, resúmenes). El crédito de cada cliente se
calcula y se cobra en la moneda de su condición, sin convertir.

    USD -> PEN:  soles   = dólares × TC
    PEN -> USD:  dólares = soles ÷ TC          (TC = soles por 1 dólar = 3.47)

El resultado se redondea a 2 decimales (mitad hacia arriba), igual que los demás montos.
"""
from decimal import Decimal

from app.core.configuracion import configuracion
from app.services.finance.finance_tasas import redondear

PEN = "PEN"
USD = "USD"


def convertir(monto: Decimal, de: str, a: str, tipo_cambio: Decimal | None = None) -> Decimal:
    tc = tipo_cambio if tipo_cambio is not None else configuracion.tipo_cambio_usd_pen
    if tc <= 0:
        raise ValueError("El tipo de cambio debe ser mayor que cero.")
    if de == a:
        return redondear(monto, 2)
    if de == USD and a == PEN:
        return redondear(monto * tc, 2)
    if de == PEN and a == USD:
        return redondear(monto / tc, 2)
    raise ValueError(f"Conversión no soportada: {de} -> {a}. Solo se manejan PEN y USD.")


def a_soles(monto: Decimal, moneda: str) -> Decimal:
    return convertir(monto, moneda, PEN)

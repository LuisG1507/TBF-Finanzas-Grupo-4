"""TCEA de los flujos programados, con año comercial de 360 días."""
from collections.abc import Iterable
from decimal import Decimal, DecimalException, localcontext

from app.services.finance.finance_tasas import CIEN, DECIMALES_TASA, redondear

ANIO_COMERCIAL = Decimal(360)
TOLERANCIA_TASA = Decimal("1e-12")


def _factor_de_varios_pagos(capital: Decimal, flujos: list[tuple[int, Decimal]]) -> Decimal:
    # Bisección en ln(1 + r). El valor actual decrece a medida que crece ese logaritmo.
    total = sum(monto for _, monto in flujos)
    if total == capital:
        return Decimal(1)

    # Si todo venciera en la primera o última fecha, la solución sería de un solo pago.
    # Esas dos tasas acotan la solución para las fechas reales, incluso si la tasa es negativa.
    log_total = (total / capital).ln() * ANIO_COMERCIAL
    primer_dia = min(dias for dias, _ in flujos)
    ultimo_dia = max(dias for dias, _ in flujos)
    inferior, superior = sorted((log_total / primer_dia, log_total / ultimo_dia))
    pagos = [(Decimal(dias) / ANIO_COMERCIAL, (monto / capital).ln()) for dias, monto in flujos]

    for _ in range(256):
        centro = (inferior + superior) / 2
        valor_actual = Decimal(0)
        for plazo, log_proporcion in pagos:
            exponente = log_proporcion - centro * plazo
            if exponente > 0:
                # Este pago solo ya supera el capital. Evita exponenciar un valor extremo.
                valor_actual = Decimal(2)
                break
            valor_actual += exponente.exp()
            if valor_actual > 1:
                break

        if valor_actual > 1:
            inferior = centro
        else:
            superior = centro
        if superior - inferior <= Decimal("1e-24") and superior.exp() - inferior.exp() <= TOLERANCIA_TASA:
            return ((inferior + superior) / 2).exp()

    raise ValueError("El cálculo de la TCEA no convergió para estos flujos.")


def calcular_tcea_pct(capital: Decimal, pagos: Iterable[tuple[int, Decimal]]) -> Decimal:
    """Recibe el capital original y pares (días 30E/360 desde la compra, importe)."""
    if not capital.is_finite() or capital <= 0:
        raise ValueError("El monto recibido debe ser mayor que cero.")
    flujos = []
    for dias, monto in pagos:
        if dias <= 0:
            raise ValueError("Todos los pagos deben quedar después de la compra en días comerciales.")
        if not monto.is_finite() or monto < 0:
            raise ValueError("El importe de cada pago debe ser mayor o igual a cero.")
        if monto > 0:
            flujos.append((dias, monto))
    if not flujos:
        raise ValueError("Debe existir al menos un pago con importe mayor que cero.")

    try:
        with localcontext() as contexto:
            contexto.prec = 64
            if len(flujos) == 1:
                dias, monto = flujos[0]
                factor = (monto / capital) ** (ANIO_COMERCIAL / dias)
            else:
                factor = _factor_de_varios_pagos(capital, flujos)
            tasa_pct = (factor - 1) * CIEN
            contexto.prec = max(contexto.prec, tasa_pct.adjusted() + DECIMALES_TASA + 2)
            tasa = redondear(tasa_pct, DECIMALES_TASA)
            return tasa.copy_abs() if tasa.is_zero() else tasa
    except DecimalException as error:
        raise ValueError("No se pudo calcular la TCEA para el rango de estos flujos.") from error

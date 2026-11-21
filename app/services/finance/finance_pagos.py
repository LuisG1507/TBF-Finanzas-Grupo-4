from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.services.finance.finance_tasas import (
    CIEN,
    DECIMALES_MONTO,
    TipoTasa,
    convertir_tasa_pct,
    redondear,
)

CERO = Decimal(0)


@dataclass(frozen=True)
class ResultadoPago:
    dias_mora: int
    tasa_mora_pct: Decimal
    interes_mora: Decimal
    total_exigible: Decimal
    aceptado: bool
    motivo: str | None
    monto_aplicado: Decimal
    aplicado_mora: Decimal
    aplicado_interes_comp: Decimal
    aplicado_capital: Decimal
    aplicado_portes: Decimal
    aplicado_seguro: Decimal
    excedente_devuelto: Decimal


def dias_360(desde: date, hasta: date) -> int:
    """Dias comerciales 30/360 (europeo): el dia 31, de cualquiera de las fechas, cuenta como 30."""
    d1 = min(desde.day, 30)
    d2 = min(hasta.day, 30)
    return (hasta.year - desde.year) * 360 + (hasta.month - desde.month) * 30 + (d2 - d1)


def calcular_dias_mora(fecha_vencimiento: date, fecha_pago: date) -> int:
    """Dias de atraso entre el vencimiento y el pago real; nunca negativo."""
    return max(dias_360(fecha_vencimiento, fecha_pago), 0)


def calcular_interes_mora(
    deuda_vencida: Decimal,
    dias_mora: int,
    tasa_pct: Decimal,
    tipo: TipoTasa,
    plazo_tasa_dias: int,
    capitalizacion_dias: int | None,
) -> tuple[Decimal, Decimal]:
    """IM = deuda vencida * tasa efectiva moratoria de los dias de atraso. Devuelve (tasa en %, interes)."""
    if dias_mora <= 0:
        return CERO, CERO
    _, tasa_dias_pct = convertir_tasa_pct(
        tasa_pct, tipo, plazo_tasa_dias, capitalizacion_dias, TipoTasa.EFECTIVA, dias_mora, None
    )
    return tasa_dias_pct, redondear(deuda_vencida * tasa_dias_pct / CIEN, DECIMALES_MONTO)


def procesar_pago(
    capital: Decimal,
    interes_comp: Decimal,
    portes: Decimal,
    seguro: Decimal,
    fecha_vencimiento: date,
    fecha_pago: date,
    monto_pagado: Decimal,
    tasa_mora_pct: Decimal,
    tipo_mora: TipoTasa,
    plazo_mora_dias: int,
    capitalizacion_mora_dias: int | None,
) -> ResultadoPago:
    """Prelacion mora -> interes compensatorio -> capital. Solo acepta la cancelacion completa:
    un pago menor al total exigible se rechaza y el excedente se devuelve."""
    dias_mora = calcular_dias_mora(fecha_vencimiento, fecha_pago)
    tasa_dias_pct, interes_mora = calcular_interes_mora(
        capital + interes_comp, dias_mora, tasa_mora_pct, tipo_mora, plazo_mora_dias, capitalizacion_mora_dias
    )
    total = capital + interes_comp + interes_mora + portes + seguro

    if monto_pagado < total:
        return ResultadoPago(
            dias_mora, tasa_dias_pct, interes_mora, total, False,
            f"Pago parcial rechazado: debe cubrir el total exigible de {total}",
            CERO, CERO, CERO, CERO, CERO, CERO, monto_pagado,
        )

    pm = min(monto_pagado, interes_mora)
    pint = min(max(monto_pagado - pm, CERO), interes_comp)
    pcap = min(max(monto_pagado - pm - pint, CERO), capital)
    return ResultadoPago(
        dias_mora, tasa_dias_pct, interes_mora, total, True, None,
        pm + pint + pcap + portes + seguro, pm, pint, pcap, portes, seguro,
        monto_pagado - total,
    )

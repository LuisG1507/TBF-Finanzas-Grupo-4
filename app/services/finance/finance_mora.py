"""Interés moratorio y compensatorio por atraso (todo lo de la mora vive SOLO en este módulo).

Fuente: Martín Senmache Sarmiento, J. M. Matemática Financiera, Cap. 5, §5.2.2.8-5.2.2.11,
fórmulas Nº34 a Nº37, pp. 114-115. Validado contra los ejercicios 5-36 (c) y 5-37 (e) del libro.

Para un pago hecho DESPUÉS del vencimiento, sobre el monto vencido (el "Valor Nominal" del libro):

    Interés moratorio     Im = Valor Nominal × TE_mora(días de atraso)           (Nº36 y Nº37)
    Interés compensatorio Ic = Valor Nominal × TE_comp(días de atraso)           (Nº34 y Nº35)

donde TE(días) es la tasa efectiva que corresponde a los días de atraso:

    Tasa efectiva  (Nº34 / Nº36):  TE(días) = (1 + TE)^(días / plazo de la tasa) − 1
    Tasa nominal   (Nº35 / Nº37):  TE(días) = (1 + TN / m)^n − 1
                                    m = plazo de la tasa / días de capitalización
                                    n = días de atraso   / días de capitalización

Además puede cobrarse una comisión fija por cobranza tardía (el libro la usa en sus ejercicios).

Total del atraso = Ic + Im + comisión.   Total a pagar = monto vencido + total del atraso.

Qué se puede cambiar sin tocar el resto del sistema (parámetros de `calcular_mora`):
  - compensatorio_sigue_corriendo: el libro lo cobra también durante el atraso (True).
  - comision_cobranza: monto fijo, 0 por defecto.
La prelación (en qué orden se reparte un pago entre mora, compensatorio y capital) NO está en el
libro y se define aparte.
"""
from dataclasses import dataclass
from decimal import Decimal

from app.services.finance import finance_tasas as tasas
from app.services.finance.finance_tasas import CIEN, DECIMALES_MONTO, DECIMALES_TASA, TipoTasa, redondear


@dataclass(frozen=True)
class TasaPorAtraso:
    """Una tasa (moratoria o compensatoria) tal como la pactó el cliente."""

    tipo: TipoTasa
    tasa_pct: Decimal
    plazo_tasa_dias: int
    capitalizacion_dias: int | None = None  # obligatoria si es NOMINAL


@dataclass(frozen=True)
class ResultadoMora:
    dias_atraso: int
    monto_vencido: Decimal
    tasa_mora_dias_pct: Decimal
    interes_moratorio: Decimal
    tasa_compensatoria_dias_pct: Decimal
    interes_compensatorio: Decimal
    comision_cobranza: Decimal
    total_atraso: Decimal
    total_a_pagar: Decimal


def tasa_efectiva_por_dias_pct(tasa: TasaPorAtraso, dias: int) -> Decimal:
    """TE(días) en %, a 7 decimales. Es el único sitio donde se distingue nominal de efectiva."""
    if dias == 0:
        return Decimal(0).quantize(Decimal(1).scaleb(-DECIMALES_TASA))
    if tasa.tipo == TipoTasa.NOMINAL:
        if not tasa.capitalizacion_dias:
            raise ValueError("Una tasa NOMINAL necesita los días de capitalización")
        m = tasas.calcular_m(tasa.plazo_tasa_dias, tasa.capitalizacion_dias)
        n = tasas.calcular_n(dias, tasa.capitalizacion_dias)
        return tasas.tasa_efectiva_plazo_pct(tasa.tasa_pct, m, n)
    exponente = Decimal(dias) / Decimal(tasa.plazo_tasa_dias)
    return redondear(((1 + tasa.tasa_pct / CIEN) ** exponente - 1) * CIEN, DECIMALES_TASA)


def interes_por_atraso(monto_vencido: Decimal, tasa: TasaPorAtraso, dias: int) -> Decimal:
    """Im (o Ic) = Valor Nominal × TE(días), a 2 decimales."""
    return redondear(monto_vencido * tasa_efectiva_por_dias_pct(tasa, dias) / CIEN, DECIMALES_MONTO)


def calcular_mora(
    monto_vencido: Decimal,
    dias_atraso: int,
    tasa_mora: TasaPorAtraso,
    tasa_compensatoria: TasaPorAtraso | None = None,
    compensatorio_sigue_corriendo: bool = True,
    comision_cobranza: Decimal = Decimal(0),
) -> ResultadoMora:
    if dias_atraso < 0:
        raise ValueError("Los días de atraso no pueden ser negativos")
    if monto_vencido <= 0:
        raise ValueError("El monto vencido debe ser mayor que cero")
    if compensatorio_sigue_corriendo and tasa_compensatoria is None:
        raise ValueError("Falta la tasa compensatoria (el compensatorio sigue corriendo durante el atraso)")

    en_mora = dias_atraso > 0
    cero_tasa = redondear(Decimal(0), DECIMALES_TASA)

    tasa_mora_dias = tasa_efectiva_por_dias_pct(tasa_mora, dias_atraso)
    interes_moratorio = interes_por_atraso(monto_vencido, tasa_mora, dias_atraso)

    if compensatorio_sigue_corriendo and tasa_compensatoria is not None:
        tasa_comp_dias = tasa_efectiva_por_dias_pct(tasa_compensatoria, dias_atraso)
        interes_comp = interes_por_atraso(monto_vencido, tasa_compensatoria, dias_atraso)
    else:
        tasa_comp_dias, interes_comp = cero_tasa, redondear(Decimal(0), DECIMALES_MONTO)

    comision = redondear(comision_cobranza, DECIMALES_MONTO) if en_mora else redondear(Decimal(0), DECIMALES_MONTO)
    total_atraso = interes_moratorio + interes_comp + comision
    return ResultadoMora(
        dias_atraso=dias_atraso,
        monto_vencido=monto_vencido,
        tasa_mora_dias_pct=tasa_mora_dias,
        interes_moratorio=interes_moratorio,
        tasa_compensatoria_dias_pct=tasa_comp_dias,
        interes_compensatorio=interes_comp,
        comision_cobranza=comision,
        total_atraso=total_atraso,
        total_a_pagar=monto_vencido + total_atraso,
    )

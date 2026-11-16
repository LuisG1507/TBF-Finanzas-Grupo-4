from dataclasses import dataclass
from decimal import Decimal

from app.services.finance.finance_tasas import (
    CIEN,
    DECIMALES_MONTO,
    TipoTasa,
    convertir_tasa_pct,
    redondear,
)


@dataclass(frozen=True)
class FilaCronograma:
    numero: int
    saldo_inicial: Decimal
    interes: Decimal
    amortizacion: Decimal
    cuota: Decimal
    saldo_final: Decimal


@dataclass(frozen=True)
class PlanFrances:
    tep_pct: Decimal
    capital_capitalizado: Decimal
    interes_gracia: Decimal
    cuota: Decimal
    interes_total: Decimal
    total_a_pagar: Decimal
    cronograma: list[FilaCronograma]


def calcular_tep_pct(
    tasa_pct: Decimal,
    tipo: TipoTasa,
    plazo_tasa_dias: int,
    capitalizacion_dias: int | None,
    periodo_pago_dias: int,
) -> Decimal:
    """TEP del periodo de pago, en %, a partir de la tasa pactada (nominal o efectiva)."""
    _, tep_pct = convertir_tasa_pct(
        tasa_pct, tipo, plazo_tasa_dias, capitalizacion_dias, TipoTasa.EFECTIVA, periodo_pago_dias, None
    )
    return tep_pct


def capitalizar_gracia(capital: Decimal, tep_pct: Decimal, dias_gracia: int, periodo_pago_dias: int) -> Decimal:
    """C' = C * (1 + TEP)^(dias de gracia / dias del periodo de pago)"""
    return capital * (1 + tep_pct / CIEN) ** (Decimal(dias_gracia) / Decimal(periodo_pago_dias))


def calcular_cuota_francesa(capital: Decimal, tep_pct: Decimal, num_cuotas: int) -> Decimal:
    """R = C * TEP * (1 + TEP)^n / ((1 + TEP)^n - 1)"""
    tep = tep_pct / CIEN
    factor = (1 + tep) ** num_cuotas
    return capital * tep * factor / (factor - 1)


def generar_cronograma(capital: Decimal, tep_pct: Decimal, num_cuotas: int, cuota: Decimal) -> tuple[list[FilaCronograma], Decimal]:
    """Por cada periodo: I = TEP * SI, A = R - I, SF = SI - A. Devuelve las filas y el interes total."""
    tep = tep_pct / CIEN
    filas = []
    saldo = capital
    interes_total = Decimal(0)
    for numero in range(1, num_cuotas + 1):
        interes = saldo * tep
        amortizacion = cuota - interes
        saldo_final = saldo - amortizacion
        interes_total += interes
        filas.append(
            FilaCronograma(
                numero=numero,
                saldo_inicial=redondear(saldo, DECIMALES_MONTO),
                interes=redondear(interes, DECIMALES_MONTO),
                amortizacion=redondear(amortizacion, DECIMALES_MONTO),
                cuota=redondear(cuota, DECIMALES_MONTO),
                # el residuo numerico de la ultima cuota no puede salir negativo
                saldo_final=redondear(max(saldo_final, Decimal(0)), DECIMALES_MONTO),
            )
        )
        saldo = saldo_final
    return filas, interes_total


def calcular_plan_frances(
    capital: Decimal,
    tasa_pct: Decimal,
    tipo: TipoTasa,
    plazo_tasa_dias: int,
    capitalizacion_dias: int | None,
    periodo_pago_dias: int,
    num_cuotas: int,
    dias_gracia: int,
) -> PlanFrances:
    tep_pct = calcular_tep_pct(tasa_pct, tipo, plazo_tasa_dias, capitalizacion_dias, periodo_pago_dias)
    capital_capitalizado = capitalizar_gracia(capital, tep_pct, dias_gracia, periodo_pago_dias)
    cuota = calcular_cuota_francesa(capital_capitalizado, tep_pct, num_cuotas)
    cronograma, interes_total = generar_cronograma(capital_capitalizado, tep_pct, num_cuotas, cuota)
    return PlanFrances(
        tep_pct=tep_pct,
        capital_capitalizado=redondear(capital_capitalizado, DECIMALES_MONTO),
        interes_gracia=redondear(capital_capitalizado - capital, DECIMALES_MONTO),
        cuota=redondear(cuota, DECIMALES_MONTO),
        interes_total=redondear(interes_total, DECIMALES_MONTO),
        total_a_pagar=redondear(cuota * num_cuotas, DECIMALES_MONTO),
        cronograma=cronograma,
    )

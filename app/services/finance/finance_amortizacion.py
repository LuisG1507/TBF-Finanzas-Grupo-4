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


def generar_cronograma(capital: Decimal, tep_pct: Decimal, num_cuotas: int, cuota: Decimal) -> list[FilaCronograma]:
    """Cronograma que CUADRA con los montos ya redondeados a 2 decimales (capital y cuota llegan redondeados).

    Por cada periodo: I = TEP * SI (redondeado), A = R - I, SF = SI - A, y el SI del periodo siguiente es
    el SF de este. Asi, en cada fila interes + amortizacion = cuota y saldo inicial - amortizacion = saldo
    final, y se puede reproducir con una calculadora a partir de la tabla.
    En la ultima cuota la amortizacion es todo el saldo que queda (SF = 0) y la cuota se ajusta
    (R = SI + I): absorbe los centimos de redondeo, como se hace en una entidad financiera."""
    tep = tep_pct / CIEN
    filas = []
    saldo = capital
    for numero in range(1, num_cuotas + 1):
        interes = redondear(saldo * tep, DECIMALES_MONTO)
        if numero == num_cuotas:
            amortizacion = saldo
            cuota_fila = amortizacion + interes
        else:
            cuota_fila = cuota
            amortizacion = min(cuota - interes, saldo)
        saldo_final = saldo - amortizacion
        filas.append(
            FilaCronograma(
                numero=numero,
                saldo_inicial=saldo,
                interes=interes,
                amortizacion=amortizacion,
                cuota=cuota_fila,
                saldo_final=saldo_final,
            )
        )
        saldo = saldo_final
    return filas


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
    capital_exacto = capitalizar_gracia(capital, tep_pct, dias_gracia, periodo_pago_dias)
    capital_capitalizado = redondear(capital_exacto, DECIMALES_MONTO)
    # la cuota se calcula con la formula completa y recien al final se redondea a centimos
    cuota = redondear(calcular_cuota_francesa(capital_exacto, tep_pct, num_cuotas), DECIMALES_MONTO)
    cronograma = generar_cronograma(capital_capitalizado, tep_pct, num_cuotas, cuota)
    # los totales son la suma de las filas: asi capital capitalizado + intereses = total a pagar, siempre
    return PlanFrances(
        tep_pct=tep_pct,
        capital_capitalizado=capital_capitalizado,
        interes_gracia=capital_capitalizado - capital,
        cuota=cuota,
        interes_total=sum((f.interes for f in cronograma), Decimal(0)),
        total_a_pagar=sum((f.cuota for f in cronograma), Decimal(0)),
        cronograma=cronograma,
    )

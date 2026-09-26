from decimal import ROUND_HALF_UP, DefaultContext, Decimal, getcontext
from enum import Enum

# Precision global para todo calculo con Decimal en la app (una sola vez, en vez
# de envolver cada funcion en "with localcontext(...)").
getcontext().prec = 40
DefaultContext.prec = 40

CIEN = Decimal(100)
DECIMALES_MONTO = 2
DECIMALES_TASA = 7

_DIAS_PERIODO = {
    "DIARIA": 1,
    "QUINCENAL": 15,
    "MENSUAL": 30,
    "BIMESTRAL": 60,
    "TRIMESTRAL": 90,
    "CUATRIMESTRAL": 120,
    "SEMESTRAL": 180,
    "ANUAL": 360,
}

_DIAS_UNIDAD_PLAZO = {
    "DIAS": 1,
    "MESES": 30,
    "BIMESTRES": 60,
    "TRIMESTRES": 90,
    "CUATRIMESTRES": 120,
    "SEMESTRES": 180,
    "ANIOS": 360,
}


class Periodo(str, Enum):
    DIARIA = "DIARIA"
    QUINCENAL = "QUINCENAL"
    MENSUAL = "MENSUAL"
    BIMESTRAL = "BIMESTRAL"
    TRIMESTRAL = "TRIMESTRAL"
    CUATRIMESTRAL = "CUATRIMESTRAL"
    SEMESTRAL = "SEMESTRAL"
    ANUAL = "ANUAL"

    @property
    def dias(self) -> int:
        return _DIAS_PERIODO[self.value]


class UnidadPlazo(str, Enum):
    DIAS = "DIAS"
    MESES = "MESES"
    BIMESTRES = "BIMESTRES"
    TRIMESTRES = "TRIMESTRES"
    CUATRIMESTRES = "CUATRIMESTRES"
    SEMESTRES = "SEMESTRES"
    ANIOS = "ANIOS"

    @property
    def dias(self) -> int:
        return _DIAS_UNIDAD_PLAZO[self.value]


class TipoTasa(str, Enum):
    NOMINAL = "NOMINAL"
    EFECTIVA = "EFECTIVA"


def redondear(valor: Decimal, decimales: int) -> Decimal:
    return valor.quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP)


def calcular_m(plazo_tasa_dias: int, capitalizacion_dias: int) -> Decimal:
    """m = plazo de la TN (dias) / dias de capitalizacion."""
    return Decimal(plazo_tasa_dias) / Decimal(capitalizacion_dias)


def calcular_n(plazo_dias: int, capitalizacion_dias: int) -> Decimal:
    """n = plazo de la operacion (dias) / dias de capitalizacion."""
    return Decimal(plazo_dias) / Decimal(capitalizacion_dias)


def periodos_a_dias(n: Decimal, capitalizacion_dias: int) -> int:
    return int(redondear(n * capitalizacion_dias, 0))


def _validar_monto_mayor(monto: Decimal, capital: Decimal) -> None:
    if monto <= capital:
        raise ValueError("El monto debe ser mayor que el capital")


# --- Interes compuesto: S = C * (1 + TN/m)^n ---

def tasa_por_periodo_pct(tn_pct: Decimal, m: Decimal) -> Decimal:
    """i = TN / m, en %."""
    return redondear(tn_pct / m, DECIMALES_TASA)


def _factor_compuesto(tn_pct: Decimal, m: Decimal) -> Decimal:
    return 1 + tasa_por_periodo_pct(tn_pct, m) / CIEN


def calcular_monto(capital: Decimal, tn_pct: Decimal, m: Decimal, n: Decimal) -> Decimal:
    """S = C * (1 + TN/m)^n"""
    return redondear(capital * _factor_compuesto(tn_pct, m) ** n, DECIMALES_MONTO)


def calcular_capital(monto: Decimal, tn_pct: Decimal, m: Decimal, n: Decimal) -> Decimal:
    """C = S / (1 + TN/m)^n"""
    return redondear(monto / _factor_compuesto(tn_pct, m) ** n, DECIMALES_MONTO)


def calcular_tasa_nominal_pct(monto: Decimal, capital: Decimal, m: Decimal, n: Decimal) -> Decimal:
    """TN = m * ((S / C)^(1/n) - 1), en %."""
    _validar_monto_mayor(monto, capital)
    tn = m * ((monto / capital) ** (1 / n) - 1)
    return redondear(tn * CIEN, DECIMALES_TASA)


def calcular_plazo_periodos(monto: Decimal, capital: Decimal, tn_pct: Decimal, m: Decimal) -> Decimal:
    """n = ln(S / C) / ln(1 + TN/m)"""
    _validar_monto_mayor(monto, capital)
    n = (monto / capital).ln() / _factor_compuesto(tn_pct, m).ln()
    return redondear(n, DECIMALES_TASA)


def tasa_efectiva_plazo_pct(tn_pct: Decimal, m: Decimal, n: Decimal) -> Decimal:
    """TE = (1 + TN/m)^n - 1, en %."""
    return redondear((_factor_compuesto(tn_pct, m) ** n - 1) * CIEN, DECIMALES_TASA)


# --- Interes simple: S = C * (1 + i*t) ---

def calcular_t(plazo_dias: int, plazo_tasa_dias: int) -> Decimal:
    """t = plazo de la operacion (dias) / plazo de la tasa (dias)."""
    return Decimal(plazo_dias) / Decimal(plazo_tasa_dias)


def calcular_interes_simple(capital: Decimal, tasa_pct: Decimal, t: Decimal) -> Decimal:
    """I = C * i * t"""
    return redondear(capital * tasa_pct / CIEN * t, DECIMALES_MONTO)


def calcular_monto_simple(capital: Decimal, tasa_pct: Decimal, t: Decimal) -> Decimal:
    """S = C + I = C * (1 + i * t)"""
    return capital + calcular_interes_simple(capital, tasa_pct, t)


def calcular_capital_simple(monto: Decimal, tasa_pct: Decimal, t: Decimal) -> Decimal:
    """C = S / (1 + i * t)"""
    return redondear(monto / (1 + tasa_pct / CIEN * t), DECIMALES_MONTO)


def calcular_tasa_simple_pct(monto: Decimal, capital: Decimal, t: Decimal) -> Decimal:
    """i = ((S / C) - 1) / t, en %."""
    _validar_monto_mayor(monto, capital)
    return redondear(((monto / capital) - 1) / t * CIEN, DECIMALES_TASA)


def calcular_plazo_simple(monto: Decimal, capital: Decimal, tasa_pct: Decimal) -> Decimal:
    """t = ((S / C) - 1) / i, en periodos de la tasa."""
    _validar_monto_mayor(monto, capital)
    return redondear(((monto / capital) - 1) / (tasa_pct / CIEN), DECIMALES_TASA)


# --- Conversion de tasas: nominal <-> efectiva, usando una efectiva como puente ---

def convertir_tasa_pct(
    tasa_pct: Decimal,
    tipo_origen: TipoTasa,
    plazo_origen_dias: int,
    capitalizacion_origen_dias: int | None,
    tipo_destino: TipoTasa,
    plazo_destino_dias: int,
    capitalizacion_destino_dias: int | None,
) -> tuple[Decimal, Decimal]:
    """Devuelve (tasa puente en %, tasa resultado en %)."""
    if tipo_origen == TipoTasa.NOMINAL:
        m_origen = calcular_m(plazo_origen_dias, capitalizacion_origen_dias)
        factor_origen = _factor_compuesto(tasa_pct, m_origen) ** m_origen
    else:
        factor_origen = 1 + tasa_pct / CIEN
    tasa_puente = redondear((factor_origen - 1) * CIEN, DECIMALES_TASA)

    factor_destino = factor_origen ** (Decimal(plazo_destino_dias) / Decimal(plazo_origen_dias))
    if tipo_destino == TipoTasa.EFECTIVA:
        resultado = (factor_destino - 1) * CIEN
    else:
        m_destino = calcular_m(plazo_destino_dias, capitalizacion_destino_dias)
        resultado = m_destino * (factor_destino ** (1 / m_destino) - 1) * CIEN
    return tasa_puente, redondear(resultado, DECIMALES_TASA)

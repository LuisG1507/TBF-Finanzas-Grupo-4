from dataclasses import asdict
from decimal import Decimal

from fastapi import APIRouter, HTTPException

from app.schemas import schemas_finanzas as esquemas
from app.services.ciclo_credito import dias_30_360
from app.services.finance import finance_amortizacion as amortizacion
from app.services.finance import finance_mora as mora
from app.services.finance import finance_pagos as pagos
from app.services.finance import finance_tasas as tasas
from app.services.finance.finance_tcea import calcular_tcea_pct

router = APIRouter(prefix="/finanzas", tags=["Calculadora financiera"])


@router.post("/tcea", response_model=esquemas.RespuestaTcea, summary="TCEA de uno o varios pagos programados")
def calcular_tcea(datos: esquemas.EntradaTcea):
    flujos = []
    for pago in datos.pagos:
        dias = pago.dias
        if pago.fecha is not None and datos.fecha_compra is not None:
            dias = dias_30_360(datos.fecha_compra, pago.fecha)
        assert dias is not None  # El esquema exige días o una fecha con su fecha de compra.
        flujos.append((dias, pago.monto))
    try:
        return esquemas.RespuestaTcea(tcea_pct=calcular_tcea_pct(datos.monto_recibido, flujos))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def _dias(periodo: tasas.Periodo | int) -> int:
    """Un periodo de la lista (ANUAL, MENSUAL...) o un numero entero de dias, ambos a dias."""
    return periodo.dias if isinstance(periodo, tasas.Periodo) else periodo


# --- Interes compuesto: S = C * (1 + TN/m)^n ---

@router.post("/compuesto/monto", response_model=esquemas.RespuestaMonto, summary="Monto: S = C * (1 + TN/m)^n")
def monto_compuesto(datos: esquemas.EntradaMonto):
    m = tasas.calcular_m(_dias(datos.plazo_tasa), _dias(datos.capitalizacion))
    n = tasas.calcular_n(datos.plazo * datos.unidad_plazo.dias, _dias(datos.capitalizacion))
    monto = tasas.calcular_monto(datos.capital, datos.tasa_nominal_pct, m, n)
    return esquemas.RespuestaMonto(
        m=tasas.redondear(m, tasas.DECIMALES_TASA),
        n=tasas.redondear(n, tasas.DECIMALES_TASA),
        tasa_periodo_pct=tasas.tasa_por_periodo_pct(datos.tasa_nominal_pct, m),
        tasa_efectiva_plazo_pct=tasas.tasa_efectiva_plazo_pct(datos.tasa_nominal_pct, m, n),
        monto=monto,
        interes=monto - datos.capital,
    )


@router.post("/compuesto/capital", response_model=esquemas.RespuestaCapital, summary="Capital: C = S / (1 + TN/m)^n")
def capital_compuesto(datos: esquemas.EntradaCapital):
    m = tasas.calcular_m(_dias(datos.plazo_tasa), _dias(datos.capitalizacion))
    n = tasas.calcular_n(datos.plazo * datos.unidad_plazo.dias, _dias(datos.capitalizacion))
    capital = tasas.calcular_capital(datos.monto, datos.tasa_nominal_pct, m, n)
    return esquemas.RespuestaCapital(
        m=tasas.redondear(m, tasas.DECIMALES_TASA),
        n=tasas.redondear(n, tasas.DECIMALES_TASA),
        tasa_periodo_pct=tasas.tasa_por_periodo_pct(datos.tasa_nominal_pct, m),
        capital=capital,
        interes=datos.monto - capital,
    )


@router.post("/compuesto/tasa-nominal", response_model=esquemas.RespuestaTasaNominal, summary="Tasa nominal: TN = m * ((S/C)^(1/n) - 1)")
def tasa_nominal_compuesto(datos: esquemas.EntradaTasaNominal):
    m = tasas.calcular_m(_dias(datos.plazo_tasa), _dias(datos.capitalizacion))
    n = tasas.calcular_n(datos.plazo * datos.unidad_plazo.dias, _dias(datos.capitalizacion))
    try:
        tn = tasas.calcular_tasa_nominal_pct(datos.monto, datos.capital, m, n)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return esquemas.RespuestaTasaNominal(
        m=tasas.redondear(m, tasas.DECIMALES_TASA), n=tasas.redondear(n, tasas.DECIMALES_TASA), tasa_nominal_pct=tn
    )


@router.post("/compuesto/plazo", response_model=esquemas.RespuestaPlazo, summary="Plazo: n = ln(S/C) / ln(1 + TN/m)")
def plazo_compuesto(datos: esquemas.EntradaPlazo):
    m = tasas.calcular_m(_dias(datos.plazo_tasa), _dias(datos.capitalizacion))
    try:
        n = tasas.calcular_plazo_periodos(datos.monto, datos.capital, datos.tasa_nominal_pct, m)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    plazo_dias = tasas.periodos_a_dias(n, _dias(datos.capitalizacion))
    return esquemas.RespuestaPlazo(
        m=tasas.redondear(m, tasas.DECIMALES_TASA),
        plazo_periodos=n,
        plazo_dias=plazo_dias,
        plazo_en_unidad=tasas.redondear(Decimal(plazo_dias) / datos.unidad_plazo.dias, 4),
    )


@router.post("/compuesto/tasa-efectiva", response_model=esquemas.RespuestaTasaEfectiva, summary="Tasa efectiva: TE = (1 + TN/m)^n - 1")
def tasa_efectiva_compuesto(datos: esquemas.EntradaTasaEfectiva):
    m = tasas.calcular_m(_dias(datos.plazo_tasa), _dias(datos.capitalizacion))
    n = tasas.calcular_n(datos.plazo * datos.unidad_plazo.dias, _dias(datos.capitalizacion))
    return esquemas.RespuestaTasaEfectiva(
        m=tasas.redondear(m, tasas.DECIMALES_TASA),
        n=tasas.redondear(n, tasas.DECIMALES_TASA),
        tasa_periodo_pct=tasas.tasa_por_periodo_pct(datos.tasa_nominal_pct, m),
        tasa_efectiva_plazo_pct=tasas.tasa_efectiva_plazo_pct(datos.tasa_nominal_pct, m, n),
    )


# --- Interes simple: S = C * (1 + i*t) ---

@router.post("/simple/interes", response_model=esquemas.RespuestaSimpleInteres, summary="Interes simple: I = C * i * t")
def interes_simple(datos: esquemas.EntradaSimpleConCapital):
    t = tasas.calcular_t(datos.plazo * datos.unidad_plazo.dias, _dias(datos.plazo_tasa))
    interes = tasas.calcular_interes_simple(datos.capital, datos.tasa_pct, t)
    return esquemas.RespuestaSimpleInteres(t=tasas.redondear(t, tasas.DECIMALES_TASA), interes=interes, monto=datos.capital + interes)


@router.post("/simple/monto", response_model=esquemas.RespuestaSimpleInteres, summary="Monto simple: S = C * (1 + i * t)")
def monto_simple(datos: esquemas.EntradaSimpleConCapital):
    t = tasas.calcular_t(datos.plazo * datos.unidad_plazo.dias, _dias(datos.plazo_tasa))
    monto = tasas.calcular_monto_simple(datos.capital, datos.tasa_pct, t)
    return esquemas.RespuestaSimpleInteres(t=tasas.redondear(t, tasas.DECIMALES_TASA), interes=monto - datos.capital, monto=monto)


@router.post("/simple/capital", response_model=esquemas.RespuestaSimpleCapital, summary="Capital simple: C = S / (1 + i * t)")
def capital_simple(datos: esquemas.EntradaSimpleConMonto):
    t = tasas.calcular_t(datos.plazo * datos.unidad_plazo.dias, _dias(datos.plazo_tasa))
    capital = tasas.calcular_capital_simple(datos.monto, datos.tasa_pct, t)
    return esquemas.RespuestaSimpleCapital(t=tasas.redondear(t, tasas.DECIMALES_TASA), capital=capital, interes=datos.monto - capital)


@router.post("/simple/tasa", response_model=esquemas.RespuestaSimpleTasa, summary="Tasa simple: i = ((S/C) - 1) / t")
def tasa_simple(datos: esquemas.EntradaSimpleTasa):
    t = tasas.calcular_t(datos.plazo * datos.unidad_plazo.dias, _dias(datos.plazo_tasa))
    try:
        tasa = tasas.calcular_tasa_simple_pct(datos.monto, datos.capital, t)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return esquemas.RespuestaSimpleTasa(t=tasas.redondear(t, tasas.DECIMALES_TASA), tasa_pct=tasa)


@router.post("/simple/plazo", response_model=esquemas.RespuestaSimplePlazo, summary="Plazo simple: t = ((S/C) - 1) / i")
def plazo_simple(datos: esquemas.EntradaSimplePlazo):
    try:
        t = tasas.calcular_plazo_simple(datos.monto, datos.capital, datos.tasa_pct)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    plazo_dias = tasas.dias_por_exceso(t * _dias(datos.plazo_tasa))
    return esquemas.RespuestaSimplePlazo(
        t=t,
        plazo_dias=plazo_dias,
        plazo_en_unidad=tasas.redondear(Decimal(plazo_dias) / datos.unidad_plazo.dias, 4),
    )


# --- Conversion de tasas: nominal o efectiva a nominal o efectiva ---

@router.post("/conversion-tasas", response_model=esquemas.RespuestaConversionTasa, summary="Conversion de tasas, usando una efectiva como puente")
def conversion_tasas(datos: esquemas.EntradaConversionTasa):
    nominal_origen = datos.tipo_origen == tasas.TipoTasa.NOMINAL
    nominal_destino = datos.tipo_destino == tasas.TipoTasa.NOMINAL
    plazo_origen = _dias(datos.plazo_origen)
    plazo_destino = _dias(datos.plazo_destino)
    cap_origen = _dias(datos.capitalizacion_origen) if nominal_origen else None
    cap_destino = _dias(datos.capitalizacion_destino) if nominal_destino else None

    puente, resultado = tasas.convertir_tasa_pct(
        datos.tasa_pct, datos.tipo_origen, plazo_origen, cap_origen, datos.tipo_destino, plazo_destino, cap_destino
    )
    return esquemas.RespuestaConversionTasa(
        m_origen=tasas.redondear(tasas.calcular_m(plazo_origen, cap_origen), tasas.DECIMALES_TASA) if nominal_origen else None,
        m_destino=tasas.redondear(tasas.calcular_m(plazo_destino, cap_destino), tasas.DECIMALES_TASA) if nominal_destino else None,
        tasa_puente_pct=puente,
        tasa_resultado_pct=resultado,
    )


# --- Mora: Im = VN * [(1 + TE)^(dias/plazo) - 1]  o  Im = VN * [(1 + TN/m)^n - 1] ---

@router.post("/mora", response_model=esquemas.RespuestaMora, summary="Interes moratorio y compensatorio por atraso (libro, formulas 34 a 37)")
def calcular_mora(datos: esquemas.EntradaMora):
    def _tasa(tipo, tasa_pct, plazo, capitalizacion) -> mora.TasaPorAtraso:
        return mora.TasaPorAtraso(
            tipo=tipo,
            tasa_pct=tasa_pct,
            plazo_tasa_dias=_dias(plazo),
            capitalizacion_dias=_dias(capitalizacion) if tipo == tasas.TipoTasa.NOMINAL else None,
        )

    tasa_mora = _tasa(datos.tipo_tasa_mora, datos.tasa_mora_pct, datos.plazo_tasa_mora, datos.capitalizacion_mora)
    tasa_comp = (
        _tasa(datos.tipo_tasa_comp, datos.tasa_comp_pct, datos.plazo_tasa_comp, datos.capitalizacion_comp)
        if datos.compensatorio_sigue_corriendo
        else None
    )
    try:
        resultado = mora.calcular_mora(
            monto_vencido=datos.monto_vencido,
            dias_atraso=datos.dias_atraso,
            tasa_mora=tasa_mora,
            tasa_compensatoria=tasa_comp,
            compensatorio_sigue_corriendo=datos.compensatorio_sigue_corriendo,
            comision_cobranza=datos.comision_cobranza,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return esquemas.RespuestaMora(**asdict(resultado))


# --- Metodo frances: R = C' * TEP * (1+TEP)^n / ((1+TEP)^n - 1) ---

@router.post("/frances", response_model=esquemas.RespuestaFrances, summary="Cronograma por metodo frances, con gracia total en dias")
def cronograma_frances(datos: esquemas.EntradaFrances):
    nominal = datos.tipo_tasa == tasas.TipoTasa.NOMINAL
    plan = amortizacion.calcular_plan_frances(
        capital=datos.capital,
        tasa_pct=datos.tasa_pct,
        tipo=datos.tipo_tasa,
        plazo_tasa_dias=_dias(datos.plazo_tasa),
        capitalizacion_dias=_dias(datos.capitalizacion) if nominal else None,
        periodo_pago_dias=_dias(datos.periodo_pago),
        num_cuotas=datos.num_cuotas,
        dias_gracia=datos.dias_gracia,
    )
    return esquemas.RespuestaFrances(**asdict(plan))


# --- Pagos: prelacion mora -> interes compensatorio -> capital; rechaza parciales, devuelve excedente ---

@router.post("/pagos", response_model=esquemas.RespuestaPago, summary="Pago: mora, interes compensatorio y capital; rechaza pagos parciales")
def registrar_pago(datos: esquemas.EntradaPago):
    nominal = datos.tipo_tasa_mora == tasas.TipoTasa.NOMINAL
    resultado = pagos.procesar_pago(
        capital=datos.capital_exigible,
        interes_comp=datos.interes_comp_exigible,
        portes=datos.portes_exigibles,
        seguro=datos.seguro_exigible,
        fecha_vencimiento=datos.fecha_vencimiento,
        fecha_pago=datos.fecha_pago,
        monto_pagado=datos.monto_pagado,
        tasa_mora_pct=datos.tasa_mora_pct,
        tipo_mora=datos.tipo_tasa_mora,
        plazo_mora_dias=_dias(datos.plazo_tasa_mora),
        capitalizacion_mora_dias=_dias(datos.capitalizacion_mora) if nominal else None,
    )
    return esquemas.RespuestaPago(**asdict(resultado))

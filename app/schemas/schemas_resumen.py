from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.models.enumeraciones import EstadoCuota
from app.schemas.schemas_clientes import CondicionRespuesta


class PosicionCliente(BaseModel):
    cliente_id: int
    moneda: str
    saldo_capital: Decimal
    saldo_capital_pen: Decimal
    mora_acumulada: Decimal
    dias_atraso: int
    situacion: Literal["AL_DIA", "POR_VENCER", "EN_MORA"]
    proximo_vencimiento: date | None = None
    monto_proximo_pago: Decimal | None = None
    saldos_cierre_previos: list[Decimal]
    saldos_cierre_previos_pen: list[Decimal]


class CobranzaSemanal(BaseModel):
    desde: date
    hasta: date
    programado: Decimal
    cobrado: Decimal


class CuotaDelMes(BaseModel):
    cliente_id: int
    fecha_vencimiento: date
    monto: Decimal
    estado: EstadoCuota


class CierreMensual(BaseModel):
    mes: date
    cuotas_programadas: Decimal
    mora_acumulada: Decimal
    clientes_activos: int


class IndicadoresTablero(BaseModel):
    saldo_por_cobrar: Decimal
    cuotas_del_mes: Decimal
    mora_acumulada: Decimal
    clientes_activos: int


class RespuestaTablero(BaseModel):
    hoy: date
    moneda_base: Literal["PEN"] = "PEN"
    kpis: IndicadoresTablero
    posiciones: list[PosicionCliente]
    cobranza_semanal: list[CobranzaSemanal]
    cuotas_del_mes: list[CuotaDelMes]
    cierres_mensuales: list[CierreMensual]


class ResumenMiCuenta(BaseModel):
    hoy: date
    tienda: str
    posicion: PosicionCliente
    condicion: CondicionRespuesta | None
    credito_disponible: Decimal | None

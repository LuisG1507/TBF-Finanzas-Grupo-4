from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enumeraciones import EstadoCuentaEstado, TipoItemEstadoCuenta
from app.schemas.schemas_clientes import MonedaResumen


class GenerarEstadosCuenta(BaseModel):
    anio: int = Field(ge=1, le=9999, examples=[2026])
    mes: int = Field(ge=1, le=12, examples=[9])


class EstadoCuentaResumen(BaseModel):
    id_estado_cuenta: int
    cliente_id: int
    cliente_nombre: str
    moneda: MonedaResumen | None
    anio: int
    mes: int
    fecha_corte: date
    fecha_pago: date
    total_capital: Decimal
    total_interes_comp: Decimal
    total_interes_mora: Decimal
    total_pagar: Decimal
    estado: EstadoCuentaEstado
    fecha_generacion: datetime


class EstadoCuentaDetalleRespuesta(BaseModel):
    id_detalle_ec: int
    compra_id: int | None
    cuota_id: int | None
    tipo_item: TipoItemEstadoCuenta
    concepto: str
    fecha_referencia: date | None
    fecha_hora_compra: datetime | None
    dias_transcurridos: int | None
    tasa_aplicada: Decimal | None
    monto: Decimal
    orden: int
    numero_cuota: int | None
    amortizacion: Decimal | None
    interes_cuota: Decimal | None


class EstadoCuentaRespuesta(EstadoCuentaResumen):
    detalles: list[EstadoCuentaDetalleRespuesta]

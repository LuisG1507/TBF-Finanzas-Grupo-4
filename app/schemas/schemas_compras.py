"""Compras a crédito (enunciado, puntos 4, 5 y 6).

Una compra puede pagarse A FIN DE MES (un solo pago, en la fecha de pago del ciclo, con los intereses de los días
entre la compra y esa fecha) o EN CUOTAS (método francés vencido, con los días de gracia capitalizados antes de
calcular la cuota). Todos los montos van en la moneda del crédito del cliente.
"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enumeraciones import EstadoCompra, EstadoCuota, ModalidadCompra
from app.schemas.schemas_clientes import MonedaResumen
from app.schemas.schemas_finanzas import TceaPct


class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ItemCompraCrear(_Base):
    producto_id: int = Field(gt=0, examples=[1])
    cantidad: Decimal = Field(gt=0, max_digits=10, decimal_places=3, description="Hasta 3 decimales (kilos, litros...)", examples=["2"])


class CompraCrear(_Base):
    """Datos para simular o registrar una compra. La tienda sale de tu sesión."""

    cliente_id: int = Field(gt=0, examples=[1])
    modalidad: ModalidadCompra = Field(description="FIN_DE_MES (un solo pago) o CUOTAS (método francés)", examples=["CUOTAS"])
    num_cuotas: int | None = Field(
        default=None, ge=1, le=120, description="Obligatorio en CUOTAS (no mayor al máximo de meses del cliente). En FIN_DE_MES no se envía.", examples=[3]
    )
    items: list[ItemCompraCrear] = Field(min_length=1, max_length=100)
    fecha_hora_compra: datetime | None = Field(
        default=None,
        description="Cuándo se hizo la compra (hora de Lima si no trae zona). Si no se indica, ahora. No puede ser futura; "
        "sirve para registrar compras anotadas en el cuaderno.",
        examples=[None],
    )

    @model_validator(mode="after")
    def _modalidad_y_cuotas(self):
        if self.modalidad == ModalidadCompra.CUOTAS and self.num_cuotas is None:
            raise ValueError("En una compra en CUOTAS hay que indicar num_cuotas")
        if self.modalidad == ModalidadCompra.FIN_DE_MES and self.num_cuotas not in (None, 1):
            raise ValueError("Una compra a FIN_DE_MES es un solo pago: no lleva num_cuotas")
        return self


class AnularCompra(_Base):
    motivo: str = Field(min_length=3, max_length=300, examples=["Se registró dos veces"])


class ClienteResumenCompra(BaseModel):
    id_cliente: int
    nombre: str
    documento: str


class ItemCompraRespuesta(BaseModel):
    producto_id: int
    codigo: str
    nombre: str
    cantidad: Decimal
    precio_unitario: Decimal  # congelado, en la moneda del crédito del cliente
    subtotal: Decimal


class CuotaRespuesta(BaseModel):
    numero: int
    fecha_vencimiento: date
    saldo_inicial: Decimal
    interes: Decimal
    amortizacion: Decimal
    monto_cuota: Decimal
    saldo_final: Decimal
    estado: EstadoCuota


class CreditoRespuesta(BaseModel):
    """Estado del crédito del cliente al momento de la compra (solo en la simulación)."""

    limite_credito: Decimal
    capital_pendiente: Decimal
    credito_disponible: Decimal
    excede_limite: bool


class CompraRespuesta(BaseModel):
    id_compra: int | None  # None en una simulación
    estado: EstadoCompra | None
    id_condicion: int  # la condición de crédito con la que se hizo (queda congelada)
    cliente: ClienteResumenCompra
    fecha_hora_compra: datetime
    modalidad: ModalidadCompra
    moneda: MonedaResumen
    items: list[ItemCompraRespuesta]
    monto_total: Decimal
    fecha_corte: date
    dias_gracia: int
    tep_aplicada: Decimal
    capital_capitalizado: Decimal
    interes_gracia: Decimal
    num_cuotas: int
    cuota: Decimal | None  # la cuota fija (solo en CUOTAS)
    fecha_primer_pago: date  # en FIN_DE_MES, la única fecha de pago
    total_intereses: Decimal
    total_a_pagar: Decimal
    tcea_pct: TceaPct | None = Field(default=None, description="Costo efectivo anual de los pagos programados, en porcentaje.")
    cronograma: list[CuotaRespuesta]  # vacío en FIN_DE_MES
    credito: CreditoRespuesta | None = None


class CompraResumen(BaseModel):
    id_compra: int
    fecha_hora_compra: datetime
    cliente: ClienteResumenCompra
    modalidad: ModalidadCompra
    moneda: MonedaResumen
    num_cuotas: int
    monto_total: Decimal
    total_a_pagar: Decimal
    fecha_primer_pago: date
    estado: EstadoCompra


class CreditoDisponibleRespuesta(BaseModel):
    moneda: MonedaResumen
    limite_credito: Decimal
    capital_pendiente: Decimal
    credito_disponible: Decimal

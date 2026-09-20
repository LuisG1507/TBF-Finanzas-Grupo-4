from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enumeraciones import EstadoCuentaEstado, TipoItemEstadoCuenta

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.compra import Compra, Cuota
    from app.models.pago import Pago


class EstadoCuenta(Base):
    __tablename__ = "estado_cuenta"

    id_estado_cuenta: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    anio: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    fecha_corte: Mapped[date] = mapped_column(Date)
    fecha_pago: Mapped[date] = mapped_column(Date)
    total_capital: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_interes_comp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_interes_mora: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_pagar: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estado: Mapped[EstadoCuentaEstado] = mapped_column(default=EstadoCuentaEstado.EMITIDO)
    fecha_generacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cliente: Mapped["Cliente"] = relationship(back_populates="estados_cuenta")
    detalles: Mapped[list["EstadoCuentaDetalle"]] = relationship(
        back_populates="estado_cuenta", order_by="EstadoCuentaDetalle.orden"
    )
    pagos: Mapped[list["Pago"]] = relationship(back_populates="estado_cuenta")


class EstadoCuentaDetalle(Base):
    __tablename__ = "estado_cuenta_detalle"

    id_detalle_ec: Mapped[int] = mapped_column(primary_key=True)
    estado_cuenta_id: Mapped[int] = mapped_column(ForeignKey("estado_cuenta.id_estado_cuenta"))
    compra_id: Mapped[int | None] = mapped_column(ForeignKey("compra.id_compra"))
    cuota_id: Mapped[int | None] = mapped_column(ForeignKey("cuota.id_cuota"))
    tipo_item: Mapped[TipoItemEstadoCuenta] = mapped_column()
    fecha_referencia: Mapped[date | None] = mapped_column(Date)
    dias_transcurridos: Mapped[int | None] = mapped_column(Integer)
    tasa_aplicada: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    orden: Mapped[int] = mapped_column(Integer)

    estado_cuenta: Mapped["EstadoCuenta"] = relationship(back_populates="detalles")
    compra: Mapped["Compra | None"] = relationship()
    cuota: Mapped["Cuota | None"] = relationship()
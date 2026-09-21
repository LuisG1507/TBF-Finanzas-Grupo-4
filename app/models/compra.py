from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enumeraciones import EstadoCompra, EstadoCuota, ModalidadCompra

if TYPE_CHECKING:
    from app.models.catalogo import Producto
    from app.models.cliente import Cliente, CondicionCredito
    from app.models.estado_cuenta import EstadoCuentaDetalle
    from app.models.pago import Pago


class Compra(Base):
    __tablename__ = "compra"

    id_compra: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    condicion_id: Mapped[int] = mapped_column(ForeignKey("condicion_credito.id_condicion"))
    fecha_hora_compra: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modalidad: Mapped[ModalidadCompra] = mapped_column()
    num_cuotas: Mapped[int] = mapped_column(Integer)
    monto_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tep_aplicada: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    fecha_corte_asignada: Mapped[date] = mapped_column(Date)
    fecha_primer_pago: Mapped[date] = mapped_column(Date)
    dias_gracia: Mapped[int] = mapped_column(Integer)
    capital_capitalizado: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estado: Mapped[EstadoCompra] = mapped_column(default=EstadoCompra.VIGENTE)

    cliente: Mapped["Cliente"] = relationship(back_populates="compras")
    condicion: Mapped["CondicionCredito"] = relationship(back_populates="compras")
    detalles: Mapped[list["DetalleCompra"]] = relationship(back_populates="compra")
    cuotas: Mapped[list["Cuota"]] = relationship(back_populates="compra")
    estado_cuenta_detalles: Mapped[list["EstadoCuentaDetalle"]] = relationship(back_populates="compra")


class DetalleCompra(Base):
    __tablename__ = "detalle_compra"

    id_detalle: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compra.id_compra"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    compra: Mapped["Compra"] = relationship(back_populates="detalles")
    producto: Mapped["Producto"] = relationship(back_populates="detalles_compra")


class Cuota(Base):
    __tablename__ = "cuota"

    id_cuota: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compra.id_compra"))
    numero_cuota: Mapped[int] = mapped_column(Integer)
    fecha_vencimiento: Mapped[date] = mapped_column(Date)
    saldo_inicial: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    interes: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amortizacion: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    monto_cuota: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    saldo_final: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estado: Mapped[EstadoCuota] = mapped_column(default=EstadoCuota.PENDIENTE)

    compra: Mapped["Compra"] = relationship(back_populates="cuotas")
    estado_cuenta_detalles: Mapped[list["EstadoCuentaDetalle"]] = relationship(back_populates="cuota")
    pagos: Mapped[list["Pago"]] = relationship(back_populates="cuota")

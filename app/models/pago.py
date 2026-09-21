from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enumeraciones import EstadoPago

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.compra import Cuota
    from app.models.estado_cuenta import EstadoCuenta
    from app.models.usuarios import Usuario


class Pago(Base):
    __tablename__ = "pago"

    id_pago: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    estado_cuenta_id: Mapped[int | None] = mapped_column(ForeignKey("estado_cuenta.id_estado_cuenta"))
    cuota_id: Mapped[int | None] = mapped_column(ForeignKey("cuota.id_cuota"))
    fecha_hora_pago: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    monto_pagado: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    monto_mora_aplicado: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    monto_interes_comp_aplicado: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    monto_capital_aplicado: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    estado: Mapped[EstadoPago] = mapped_column(default=EstadoPago.REGISTRADO)

    cliente: Mapped["Cliente"] = relationship(back_populates="pagos")
    usuario: Mapped["Usuario"] = relationship(back_populates="pagos_registrados")
    estado_cuenta: Mapped["EstadoCuenta | None"] = relationship(back_populates="pagos")
    cuota: Mapped["Cuota | None"] = relationship(back_populates="pagos")

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enumeraciones import TipoTasa

if TYPE_CHECKING:
    from app.models.catalogo import Moneda
    from app.models.compra import Compra
    from app.models.estado_cuenta import EstadoCuenta
    from app.models.pago import Pago
    from app.models.tienda import Tienda
    from app.models.usuarios import Usuario


class Cliente(Base):
    __tablename__ = "cliente"

    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id_tienda"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), unique=True)
    tipo_documento: Mapped[str] = mapped_column(String(20))
    numero_documento: Mapped[str] = mapped_column(String(20))
    nombres: Mapped[str] = mapped_column(String(150))
    apellidos: Mapped[str] = mapped_column(String(150))
    direccion: Mapped[str | None] = mapped_column(String(255))
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tienda: Mapped["Tienda"] = relationship(back_populates="clientes")
    usuario: Mapped["Usuario"] = relationship(back_populates="cliente")
    condiciones_credito: Mapped[list["CondicionCredito"]] = relationship(back_populates="cliente")
    compras: Mapped[list["Compra"]] = relationship(back_populates="cliente")
    estados_cuenta: Mapped[list["EstadoCuenta"]] = relationship(back_populates="cliente")
    pagos: Mapped[list["Pago"]] = relationship(back_populates="cliente")


class CondicionCredito(Base):
    __tablename__ = "condicion_credito"

    id_condicion: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    moneda_id: Mapped[int] = mapped_column(ForeignKey("moneda.id_moneda"))
    tasa_compensatoria: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    tipo_tasa_comp: Mapped[TipoTasa] = mapped_column()
    plazo_tasa_comp_dias: Mapped[int] = mapped_column(Integer)
    capitaliz_comp_dias: Mapped[int | None] = mapped_column(Integer)
    tasa_moratoria: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    tipo_tasa_mora: Mapped[TipoTasa] = mapped_column()
    plazo_tasa_mora_dias: Mapped[int] = mapped_column(Integer)
    capitaliz_mora_dias: Mapped[int | None] = mapped_column(Integer)
    limite_credito: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    max_meses: Mapped[int] = mapped_column(Integer)
    dia_corte: Mapped[int] = mapped_column(Integer)
    dia_pago: Mapped[int] = mapped_column(Integer)
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date)

    cliente: Mapped["Cliente"] = relationship(back_populates="condiciones_credito")
    moneda: Mapped["Moneda"] = relationship(back_populates="condiciones_credito")
    compras: Mapped[list["Compra"]] = relationship(back_populates="condicion")

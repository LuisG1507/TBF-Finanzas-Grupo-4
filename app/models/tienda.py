from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.catalogo import Marca, Producto, Proveedor
    from app.models.cliente import Cliente
    from app.models.usuarios import Usuario


class Tienda(Base):
    __tablename__ = "tienda"

    id_tienda: Mapped[int] = mapped_column(primary_key=True)
    ruc: Mapped[str] = mapped_column(String(20), unique=True)
    razon_social: Mapped[str] = mapped_column(String(200))
    nombre_comercial: Mapped[str] = mapped_column(String(200))
    giro: Mapped[str] = mapped_column(String(100))
    direccion: Mapped[str | None] = mapped_column(String(255))
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="tienda")
    proveedores: Mapped[list["Proveedor"]] = relationship(back_populates="tienda")
    marcas: Mapped[list["Marca"]] = relationship(back_populates="tienda")
    productos: Mapped[list["Producto"]] = relationship(back_populates="tienda")
    clientes: Mapped[list["Cliente"]] = relationship(back_populates="tienda")

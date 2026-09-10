from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enumeraciones import RolCodigo

if TYPE_CHECKING:
    from app.models.bitacora import Bitacora
    from app.models.cliente import Cliente
    from app.models.pago import Pago
    from app.models.tienda import Tienda


class Rol(Base):
    __tablename__ = "rol"

    id_rol: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[RolCodigo] = mapped_column(unique=True)
    nombre: Mapped[str] = mapped_column(String(100))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id_rol"))
    tienda_id: Mapped[int | None] = mapped_column(ForeignKey("tienda.id_tienda"))
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rol: Mapped["Rol"] = relationship(back_populates="usuarios")
    tienda: Mapped["Tienda | None"] = relationship(back_populates="usuarios")
    cliente: Mapped["Cliente | None"] = relationship(back_populates="usuario", uselist=False)
    pagos_registrados: Mapped[list["Pago"]] = relationship(back_populates="usuario")
    bitacora_entradas: Mapped[list["Bitacora"]] = relationship(back_populates="usuario")

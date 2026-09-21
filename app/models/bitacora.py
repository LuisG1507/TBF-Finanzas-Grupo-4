from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enumeraciones import AccionBitacora, EntidadBitacora

if TYPE_CHECKING:
    from app.models.usuarios import Usuario


class Bitacora(Base):
    __tablename__ = "bitacora"

    id_bitacora: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    entidad: Mapped[EntidadBitacora] = mapped_column()
    entidad_id: Mapped[int] = mapped_column(Integer)
    accion: Mapped[AccionBitacora] = mapped_column()
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    detalle: Mapped[dict | None] = mapped_column(JSON)

    usuario: Mapped["Usuario"] = relationship(back_populates="bitacora_entradas")

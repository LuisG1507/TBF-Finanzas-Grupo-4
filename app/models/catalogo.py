from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.cliente import CondicionCredito
    from app.models.compra import DetalleCompra
    from app.models.tienda import Tienda


class Moneda(Base):
    __tablename__ = "moneda"

    id_moneda: Mapped[int] = mapped_column(primary_key=True)
    codigo_iso: Mapped[str] = mapped_column(String(3), unique=True)
    nombre: Mapped[str] = mapped_column(String(50))
    simbolo: Mapped[str] = mapped_column(String(5))

    condiciones_credito: Mapped[list["CondicionCredito"]] = relationship(back_populates="moneda")


class UnidadMedida(Base):
    __tablename__ = "unidad_medida"

    id_unidad: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True)
    nombre: Mapped[str] = mapped_column(String(50))

    productos: Mapped[list["Producto"]] = relationship(back_populates="unidad")


class Proveedor(Base):
    __tablename__ = "proveedor"

    id_proveedor: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id_tienda"))
    razon_social: Mapped[str] = mapped_column(String(200))
    ruc: Mapped[str | None] = mapped_column(String(20))
    telefono: Mapped[str | None] = mapped_column(String(30))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    tienda: Mapped["Tienda"] = relationship(back_populates="proveedores")
    productos: Mapped[list["Producto"]] = relationship(back_populates="proveedor")


class Marca(Base):
    __tablename__ = "marca"

    id_marca: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id_tienda"))
    nombre: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    tienda: Mapped["Tienda"] = relationship(back_populates="marcas")
    productos: Mapped[list["Producto"]] = relationship(back_populates="marca")


class Producto(Base):
    __tablename__ = "producto"

    id_producto: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id_tienda"))
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedor.id_proveedor"))
    marca_id: Mapped[int | None] = mapped_column(ForeignKey("marca.id_marca"))
    unidad_id: Mapped[int] = mapped_column(ForeignKey("unidad_medida.id_unidad"))
    codigo: Mapped[str] = mapped_column(String(50))
    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    imagen_url: Mapped[str | None] = mapped_column(String(500))
    precio_contado: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    precio_lista: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    permite_fin_de_mes: Mapped[bool] = mapped_column(Boolean, default=True)
    permite_cuotas: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    tienda: Mapped["Tienda"] = relationship(back_populates="productos")
    proveedor: Mapped["Proveedor | None"] = relationship(back_populates="productos")
    marca: Mapped["Marca | None"] = relationship(back_populates="productos")
    unidad: Mapped["UnidadMedida"] = relationship(back_populates="productos")
    detalles_compra: Mapped[list["DetalleCompra"]] = relationship(back_populates="producto")

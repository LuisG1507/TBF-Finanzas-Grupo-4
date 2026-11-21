"""Marcas, proveedores y unidades de medida (catálogos de apoyo de los productos)."""
from pydantic import BaseModel, ConfigDict, Field

_PATRON_RUC = r"^\d{11}$"
_PATRON_TELEFONO = r"^[0-9+()\-\s]{6,30}$"


class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


# --- Unidades de medida (catálogo fijo, solo lectura) ---

class UnidadRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_unidad: int
    codigo: str
    nombre: str


# --- Marcas ---

class MarcaCrear(_Base):
    nombre: str = Field(min_length=1, max_length=100, examples=["Gloria"])


class MarcaActualizar(_Base):
    nombre: str = Field(min_length=1, max_length=100)


class MarcaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_marca: int
    nombre: str
    activo: bool


# --- Proveedores ---

class ProveedorCrear(_Base):
    razon_social: str = Field(min_length=1, max_length=200, examples=["Distribuidora Santa Rosa S.A.C."])
    ruc: str | None = Field(default=None, pattern=_PATRON_RUC, description="11 dígitos", examples=["20601234567"])
    telefono: str | None = Field(default=None, pattern=_PATRON_TELEFONO, examples=["014445566"])


class ProveedorActualizar(_Base):
    razon_social: str | None = Field(default=None, min_length=1, max_length=200)
    ruc: str | None = Field(default=None, pattern=_PATRON_RUC)
    telefono: str | None = Field(default=None, pattern=_PATRON_TELEFONO)


class ProveedorRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_proveedor: int
    razon_social: str
    ruc: str | None
    telefono: str | None
    activo: bool

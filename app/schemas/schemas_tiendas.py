from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.seguridad import MAX_BYTES_PASSWORD
from app.models.enumeraciones import RolCodigo

_PATRON_RUC = r"^\d{11}$"
_PATRON_TELEFONO = r"^[0-9+()\-\s]{6,30}$"
_PATRON_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
_PATRON_USUARIO = r"^[A-Za-z0-9._-]{3,100}$"


class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class TiendaCrear(_Base):
    """Alta de una tienda, junto con las credenciales de su administrador (enunciado, punto 1)."""

    ruc: str = Field(pattern=_PATRON_RUC, description="11 dígitos", examples=["20512345678"])
    razon_social: str = Field(min_length=1, max_length=200, examples=["Bodega Don Rosendo S.A.C."])
    nombre_comercial: str = Field(min_length=1, max_length=200, examples=["Bodega Don Rosendo"])
    giro: str = Field(min_length=1, max_length=100, description="bodega, panadería, peluquería, spa...", examples=["bodega"])
    direccion: str | None = Field(default=None, max_length=255, examples=["Av. Los Olivos 123, Los Olivos"])
    telefono: str | None = Field(default=None, pattern=_PATRON_TELEFONO, examples=["987654321"])
    email: str | None = Field(default=None, max_length=150, pattern=_PATRON_EMAIL, examples=["contacto@donrosendo.pe"])

    admin_username: str = Field(
        pattern=_PATRON_USUARIO, description="Usuario del administrador del negocio (3 a 100 caracteres: letras, números, . _ -)", examples=["admin.bodega"]
    )
    admin_password: str = Field(min_length=8, description="Contraseña del administrador (mínimo 8; se guarda con bcrypt)", examples=["Bodega123"])

    @field_validator("admin_password")
    @classmethod
    def _password_no_excede_bcrypt(cls, valor: str) -> str:
        if len(valor.encode("utf-8")) > MAX_BYTES_PASSWORD:
            raise ValueError(f"La contraseña no puede pasar de {MAX_BYTES_PASSWORD} bytes")
        return valor


class TiendaActualizar(_Base):
    """Cambio parcial: solo se modifican los campos que se envían."""

    ruc: str | None = Field(default=None, pattern=_PATRON_RUC)
    razon_social: str | None = Field(default=None, min_length=1, max_length=200)
    nombre_comercial: str | None = Field(default=None, min_length=1, max_length=200)
    giro: str | None = Field(default=None, min_length=1, max_length=100)
    direccion: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, pattern=_PATRON_TELEFONO)
    email: str | None = Field(default=None, max_length=150, pattern=_PATRON_EMAIL)


class TiendaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_tienda: int
    ruc: str
    razon_social: str
    nombre_comercial: str
    giro: str
    direccion: str | None
    telefono: str | None
    email: str | None
    activo: bool
    fecha_registro: datetime


class AdministradorCreado(BaseModel):
    id_usuario: int
    username: str
    rol: RolCodigo


class TiendaCreadaRespuesta(BaseModel):
    tienda: TiendaRespuesta
    administrador: AdministradorCreado

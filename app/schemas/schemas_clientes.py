"""Clientes de una tienda y su condición de crédito (enunciado, punto 3).

Las tasas se guardan y se muestran en % con hasta 7 decimales (Anexo A), igual que en el motor financiero:
24 significa 24 %. `plazo_tasa` y `capitalizacion` aceptan lo mismo que la calculadora: un período
(ANUAL, SEMESTRAL, TRIMESTRAL, MENSUAL...) o un número de días.
"""
import re
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.seguridad import MAX_BYTES_PASSWORD
from app.schemas.schemas_finanzas import PeriodoODias
from app.services.finance.finance_tasas import Periodo, TipoTasa

_PATRON_TELEFONO = r"^[0-9+()\-\s]{6,30}$"
_PATRON_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
_PATRON_USUARIO = r"^[A-Za-z0-9._-]{3,100}$"

CAPITALIZACION_POR_DEFECTO_DIAS = 30  # decisión del equipo: si no se indica, la capitalización es mensual


class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class TipoDocumento(str, Enum):
    DNI = "DNI"
    CE = "CE"  # carnet de extranjería
    RUC = "RUC"
    PASAPORTE = "PASAPORTE"


_FORMATO_DOCUMENTO = {
    TipoDocumento.DNI: (r"^\d{8}$", "8 dígitos"),
    TipoDocumento.RUC: (r"^\d{11}$", "11 dígitos"),
    TipoDocumento.CE: (r"^[A-Za-z0-9]{9,12}$", "9 a 12 letras o números"),
    TipoDocumento.PASAPORTE: (r"^[A-Za-z0-9]{6,12}$", "6 a 12 letras o números"),
}


def validar_documento(tipo: TipoDocumento, numero: str) -> str:
    """Devuelve el número normalizado (mayúsculas) o lanza ValueError con el formato esperado."""
    patron, descripcion = _FORMATO_DOCUMENTO[tipo]
    if not re.match(patron, numero):
        raise ValueError(f"El número de documento de un {tipo.value} debe tener {descripcion}")
    return numero.upper()


def _dias(valor: Periodo | int) -> int:
    return valor.dias if isinstance(valor, Periodo) else valor


def _validar_password(valor: str) -> str:
    if len(valor.encode("utf-8")) > MAX_BYTES_PASSWORD:
        raise ValueError(f"La contraseña no puede pasar de {MAX_BYTES_PASSWORD} bytes")
    return valor


# ---------------------------------------------------------------- condición de crédito

class TasaPactada(_Base):
    """Una tasa pactada con el cliente (compensatoria o moratoria): nominal o efectiva."""

    tipo: TipoTasa = Field(examples=["NOMINAL"])
    tasa_pct: Decimal = Field(gt=0, max_digits=10, decimal_places=7, description="En %: 24 significa 24 %", examples=["24"])
    plazo_tasa: PeriodoODias = Field(description="Plazo en que está expresada la tasa", examples=["ANUAL"])
    capitalizacion: PeriodoODias | None = Field(
        default=None,
        description="Solo para tasas NOMINALES. Si no se indica, 30 días (mensual). En tasas EFECTIVAS no aplica.",
        examples=[None, "MENSUAL"],
    )

    @model_validator(mode="after")
    def _coherencia(self):
        if self.tipo == TipoTasa.EFECTIVA:
            if self.capitalizacion is not None:
                raise ValueError("La capitalización no aplica a una tasa EFECTIVA")
        else:
            if self.capitalizacion is None:
                self.capitalizacion = CAPITALIZACION_POR_DEFECTO_DIAS
            if _dias(self.capitalizacion) > _dias(self.plazo_tasa):
                raise ValueError("La capitalización no puede ser más larga que el plazo de la tasa")
        return self

    @property
    def plazo_dias(self) -> int:
        return _dias(self.plazo_tasa)

    @property
    def capitalizacion_dias(self) -> int | None:
        return None if self.capitalizacion is None else _dias(self.capitalizacion)


class CondicionCrear(_Base):
    moneda: str = Field(pattern=r"^[A-Z]{3}$", description="Código de la moneda del crédito: PEN o USD (ver GET /monedas)", examples=["PEN"])
    tasa_compensatoria: TasaPactada
    tasa_moratoria: TasaPactada
    limite_credito: Decimal = Field(gt=0, max_digits=12, decimal_places=2, description="Máximo que puede deber (saldo de capital pendiente)", examples=["1500.00"])
    max_meses: int = Field(ge=1, le=120, description="Máximo número de meses (cuotas) en que se le puede dar crédito", examples=[6])
    dia_corte: int = Field(ge=1, le=28, description="Día del mes en que se cierra el ciclo de compras", examples=[20])
    dia_pago: int = Field(ge=1, le=28, description="Día del mes en que se compromete a pagar", examples=[26])
    hora_corte: time = Field(default=time(0, 0), description="Hora del día de corte (por defecto 00:00)", examples=["00:00"])
    vigente_desde: date | None = Field(
        default=None,
        description="Desde cuándo rige esta condición. Si no se indica, hoy (hora de Lima). No puede ser futura; "
        "sirve para cargar clientes que ya compraban antes de entrar al sistema.",
        examples=[None],
    )


class MonedaResumen(BaseModel):
    codigo_iso: str
    simbolo: str


class TasaPactadaRespuesta(BaseModel):
    tipo: TipoTasa
    tasa_pct: Decimal
    plazo_dias: int
    capitalizacion_dias: int | None


class CondicionRespuesta(BaseModel):
    id_condicion: int
    moneda: MonedaResumen
    tasa_compensatoria: TasaPactadaRespuesta
    tasa_moratoria: TasaPactadaRespuesta
    limite_credito: Decimal
    max_meses: int
    dia_corte: int
    hora_corte: time
    dia_pago: int
    vigente_desde: date
    vigente_hasta: date | None  # None = es la condición vigente


# ---------------------------------------------------------------- cliente

class ClienteCrear(_Base):
    """Alta de un cliente: datos generales, su acceso al sistema y su condición de crédito."""

    tipo_documento: TipoDocumento = Field(examples=["DNI"])
    numero_documento: str = Field(min_length=6, max_length=20, examples=["70000001"])
    nombres: str = Field(min_length=1, max_length=150, examples=["Ana María"])
    apellidos: str = Field(min_length=1, max_length=150, examples=["Quispe Rojas"])
    direccion: str | None = Field(default=None, max_length=255, examples=["Jr. Los Pinos 456"])
    telefono: str | None = Field(default=None, pattern=_PATRON_TELEFONO, examples=["987111222"])
    email: str | None = Field(default=None, max_length=150, pattern=_PATRON_EMAIL, examples=["ana@correo.pe"])

    usuario: str | None = Field(
        default=None, pattern=_PATRON_USUARIO,
        description="Usuario con el que entrará. Si no se indica, será su número de documento.",
    )
    password: str = Field(min_length=8, description="Contraseña inicial (mínimo 8; se guarda con bcrypt)", examples=["Cliente123"])
    condicion: CondicionCrear

    @field_validator("password")
    @classmethod
    def _password(cls, valor: str) -> str:
        return _validar_password(valor)

    @model_validator(mode="after")
    def _documento(self):
        self.numero_documento = validar_documento(self.tipo_documento, self.numero_documento)
        return self


class ClienteActualizar(_Base):
    """Cambio parcial de los datos generales. La condición de crédito se cambia aparte (PUT .../condicion)."""

    tipo_documento: TipoDocumento | None = None
    numero_documento: str | None = Field(default=None, min_length=6, max_length=20)
    nombres: str | None = Field(default=None, min_length=1, max_length=150)
    apellidos: str | None = Field(default=None, min_length=1, max_length=150)
    direccion: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, pattern=_PATRON_TELEFONO)
    email: str | None = Field(default=None, max_length=150, pattern=_PATRON_EMAIL)


class NuevaPassword(_Base):
    nueva_password: str = Field(min_length=8, examples=["NuevaClave123"])

    @field_validator("nueva_password")
    @classmethod
    def _password(cls, valor: str) -> str:
        return _validar_password(valor)


class ClienteRespuesta(BaseModel):
    id_cliente: int
    tipo_documento: str
    numero_documento: str
    nombres: str
    apellidos: str
    direccion: str | None
    telefono: str | None
    email: str | None
    activo: bool
    fecha_registro: datetime
    usuario: str
    condicion: CondicionRespuesta | None  # la condición vigente

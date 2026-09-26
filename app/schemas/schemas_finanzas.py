from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from app.services.finance.finance_tasas import Periodo, TipoTasa, UnidadPlazo

PeriodoODias = Periodo | Annotated[int, Field(gt=0)]


# --- Interes compuesto ---

class EntradaMonto(BaseModel):
    capital: Decimal = Field(gt=0, decimal_places=2, examples=["1000.00"])
    tasa_nominal_pct: Decimal = Field(gt=0, decimal_places=4, examples=["24.0000"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    capitalizacion: PeriodoODias = Field(examples=["MENSUAL", 45])
    plazo: int = Field(gt=0, examples=[3])
    unidad_plazo: UnidadPlazo = Field(examples=["MESES"])


class EntradaCapital(BaseModel):
    monto: Decimal = Field(gt=0, decimal_places=2, examples=["1061.21"])
    tasa_nominal_pct: Decimal = Field(gt=0, decimal_places=4, examples=["24.0000"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    capitalizacion: PeriodoODias = Field(examples=["MENSUAL", 45])
    plazo: int = Field(gt=0, examples=[3])
    unidad_plazo: UnidadPlazo = Field(examples=["MESES"])


class EntradaTasaEfectiva(BaseModel):
    tasa_nominal_pct: Decimal = Field(gt=0, decimal_places=4, examples=["24.0000"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    capitalizacion: PeriodoODias = Field(examples=["MENSUAL", 45])
    plazo: int = Field(gt=0, examples=[3])
    unidad_plazo: UnidadPlazo = Field(examples=["MESES"])


class EntradaTasaNominal(BaseModel):
    capital: Decimal = Field(gt=0, decimal_places=2, examples=["1000.00"])
    monto: Decimal = Field(gt=0, decimal_places=2, examples=["1061.21"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    capitalizacion: PeriodoODias = Field(examples=["MENSUAL", 45])
    plazo: int = Field(gt=0, examples=[3])
    unidad_plazo: UnidadPlazo = Field(examples=["MESES"])


class EntradaPlazo(BaseModel):
    capital: Decimal = Field(gt=0, decimal_places=2, examples=["1000.00"])
    monto: Decimal = Field(gt=0, decimal_places=2, examples=["1061.21"])
    tasa_nominal_pct: Decimal = Field(gt=0, decimal_places=4, examples=["24.0000"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    capitalizacion: PeriodoODias = Field(examples=["MENSUAL", 45])
    unidad_plazo: UnidadPlazo = Field(default=UnidadPlazo.DIAS, examples=["MESES"])


class RespuestaMonto(BaseModel):
    m: Decimal
    n: Decimal
    tasa_periodo_pct: Decimal
    tasa_efectiva_plazo_pct: Decimal
    monto: Decimal
    interes: Decimal


class RespuestaCapital(BaseModel):
    m: Decimal
    n: Decimal
    tasa_periodo_pct: Decimal
    capital: Decimal
    interes: Decimal


class RespuestaTasaNominal(BaseModel):
    m: Decimal
    n: Decimal
    tasa_nominal_pct: Decimal


class RespuestaPlazo(BaseModel):
    m: Decimal
    plazo_periodos: Decimal
    plazo_dias: int
    plazo_en_unidad: Decimal


class RespuestaTasaEfectiva(BaseModel):
    m: Decimal
    n: Decimal
    tasa_periodo_pct: Decimal
    tasa_efectiva_plazo_pct: Decimal


# --- Interes simple ---

class EntradaSimpleConCapital(BaseModel):
    capital: Decimal = Field(gt=0, decimal_places=2, examples=["50000.00"])
    tasa_pct: Decimal = Field(gt=0, decimal_places=4, examples=["8.0000"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    plazo: int = Field(gt=0, examples=[236])
    unidad_plazo: UnidadPlazo = Field(examples=["DIAS"])


class EntradaSimpleConMonto(BaseModel):
    monto: Decimal = Field(gt=0, decimal_places=2, examples=["52622.22"])
    tasa_pct: Decimal = Field(gt=0, decimal_places=4, examples=["8.0000"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    plazo: int = Field(gt=0, examples=[236])
    unidad_plazo: UnidadPlazo = Field(examples=["DIAS"])


class EntradaSimpleTasa(BaseModel):
    capital: Decimal = Field(gt=0, decimal_places=2, examples=["50000.00"])
    monto: Decimal = Field(gt=0, decimal_places=2, examples=["52622.22"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    plazo: int = Field(gt=0, examples=[236])
    unidad_plazo: UnidadPlazo = Field(examples=["DIAS"])


class EntradaSimplePlazo(BaseModel):
    capital: Decimal = Field(gt=0, decimal_places=2, examples=["50000.00"])
    monto: Decimal = Field(gt=0, decimal_places=2, examples=["52622.22"])
    tasa_pct: Decimal = Field(gt=0, decimal_places=4, examples=["8.0000"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    unidad_plazo: UnidadPlazo = Field(default=UnidadPlazo.DIAS, examples=["DIAS"])


class RespuestaSimpleInteres(BaseModel):
    t: Decimal
    interes: Decimal
    monto: Decimal


class RespuestaSimpleCapital(BaseModel):
    t: Decimal
    capital: Decimal
    interes: Decimal


class RespuestaSimpleTasa(BaseModel):
    t: Decimal
    tasa_pct: Decimal


class RespuestaSimplePlazo(BaseModel):
    t: Decimal
    plazo_dias: int
    plazo_en_unidad: Decimal


# TASASSSS

class EntradaConversionTasa(BaseModel):
    tipo_origen: TipoTasa = Field(examples=["NOMINAL"])
    tasa_pct: Decimal = Field(gt=0, decimal_places=4, examples=["18.0000"])
    plazo_origen: PeriodoODias = Field(examples=["ANUAL", 236])
    capitalizacion_origen: PeriodoODias | None = Field(default=None, examples=["DIARIA"])
    tipo_destino: TipoTasa = Field(examples=["NOMINAL"])
    plazo_destino: PeriodoODias = Field(examples=["BIMESTRAL", 45])
    capitalizacion_destino: PeriodoODias | None = Field(default=None, examples=["MENSUAL"])

    @model_validator(mode="after")
    def exigir_capitalizacion_si_es_nominal(self):
        if self.tipo_origen == TipoTasa.NOMINAL and self.capitalizacion_origen is None:
            raise ValueError("capitalizacion_origen es obligatoria cuando tipo_origen es NOMINAL")
        if self.tipo_destino == TipoTasa.NOMINAL and self.capitalizacion_destino is None:
            raise ValueError("capitalizacion_destino es obligatoria cuando tipo_destino es NOMINAL")
        return self


class RespuestaConversionTasa(BaseModel):
    m_origen: Decimal | None
    m_destino: Decimal | None
    tasa_puente_pct: Decimal
    tasa_resultado_pct: Decimal

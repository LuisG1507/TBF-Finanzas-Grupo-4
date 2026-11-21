from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_serializer, model_validator

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


# --- Metodo frances ---

class EntradaFrances(BaseModel):
    capital: Decimal = Field(gt=0, decimal_places=2, examples=["1000.00"])
    tipo_tasa: TipoTasa = Field(examples=["NOMINAL"])
    tasa_pct: Decimal = Field(gt=0, decimal_places=4, examples=["24.0000"])
    plazo_tasa: PeriodoODias = Field(examples=["ANUAL", 236])
    capitalizacion: PeriodoODias | None = Field(default=None, examples=["MENSUAL"])
    periodo_pago: PeriodoODias = Field(default=Periodo.MENSUAL, examples=["MENSUAL", "SEMESTRAL"])
    num_cuotas: int = Field(gt=0, examples=[3])
    dias_gracia: int = Field(default=0, ge=0, examples=[11])

    @model_validator(mode="after")
    def exigir_capitalizacion_si_es_nominal(self):
        if self.tipo_tasa == TipoTasa.NOMINAL and self.capitalizacion is None:
            raise ValueError("capitalizacion es obligatoria cuando tipo_tasa es NOMINAL")
        return self


# --- Mora (libro de Senmache, fórmulas Nº34 a Nº37) ---

class EntradaMora(BaseModel):
    monto_vencido: Decimal = Field(gt=0, decimal_places=2, examples=["20000.00"])
    dias_atraso: int = Field(ge=0, examples=[7])

    tipo_tasa_mora: TipoTasa = Field(examples=["EFECTIVA"])
    tasa_mora_pct: Decimal = Field(gt=0, decimal_places=4, examples=["60.0000"])
    plazo_tasa_mora: PeriodoODias = Field(examples=["ANUAL", 236])
    capitalizacion_mora: PeriodoODias | None = Field(default=None, examples=[None, "DIARIA"])

    compensatorio_sigue_corriendo: bool = Field(default=True, description="El libro cobra el compensatorio también durante el atraso")
    tipo_tasa_comp: TipoTasa | None = Field(default=None, examples=["NOMINAL"])
    tasa_comp_pct: Decimal | None = Field(default=None, gt=0, decimal_places=4, examples=["20.0000"])
    plazo_tasa_comp: PeriodoODias | None = Field(default=None, examples=["ANUAL"])
    capitalizacion_comp: PeriodoODias | None = Field(default=None, examples=["DIARIA"])

    comision_cobranza: Decimal = Field(default=Decimal(0), ge=0, decimal_places=2, examples=["50.00"])

    @model_validator(mode="after")
    def validar_tasas(self):
        if self.tipo_tasa_mora == TipoTasa.NOMINAL and self.capitalizacion_mora is None:
            raise ValueError("capitalizacion_mora es obligatoria cuando tipo_tasa_mora es NOMINAL")
        if self.compensatorio_sigue_corriendo:
            if self.tipo_tasa_comp is None or self.tasa_comp_pct is None or self.plazo_tasa_comp is None:
                raise ValueError("tipo_tasa_comp, tasa_comp_pct y plazo_tasa_comp son obligatorios mientras el compensatorio siga corriendo")
            if self.tipo_tasa_comp == TipoTasa.NOMINAL and self.capitalizacion_comp is None:
                raise ValueError("capitalizacion_comp es obligatoria cuando tipo_tasa_comp es NOMINAL")
        return self


class RespuestaMora(BaseModel):
    dias_atraso: int
    monto_vencido: Decimal
    tasa_mora_dias_pct: Decimal
    interes_moratorio: Decimal
    tasa_compensatoria_dias_pct: Decimal
    interes_compensatorio: Decimal
    comision_cobranza: Decimal
    total_atraso: Decimal
    total_a_pagar: Decimal

    @field_serializer("tasa_mora_dias_pct", "tasa_compensatoria_dias_pct")
    def _tasa_sin_notacion_cientifica(self, valor: Decimal) -> str:
        return format(valor, "f")  # 0.0000000 en vez de 0E-7


class FilaCronograma(BaseModel):
    numero: int
    saldo_inicial: Decimal
    interes: Decimal
    amortizacion: Decimal
    cuota: Decimal
    saldo_final: Decimal


class RespuestaFrances(BaseModel):
    tep_pct: Decimal
    capital_capitalizado: Decimal
    interes_gracia: Decimal
    cuota: Decimal
    interes_total: Decimal
    total_a_pagar: Decimal
    cronograma: list[FilaCronograma]

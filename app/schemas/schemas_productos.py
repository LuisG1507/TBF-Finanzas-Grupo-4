from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Imagen: una dirección web (http/https) o una ruta propia del sistema que empiece con "/".
_PATRON_IMAGEN = r"^(https?://|/)\S+$"
_PATRON_CODIGO = r"^[A-Za-z0-9._\-/]{1,50}$"


class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


def _precio(**extra):
    return Field(gt=0, max_digits=12, decimal_places=2, **extra)


class ProductoCrear(_Base):
    """Alta de un producto o servicio."""

    codigo: str = Field(pattern=_PATRON_CODIGO, description="Único dentro de la tienda", examples=["ARR-001"])
    nombre: str = Field(min_length=1, max_length=200, examples=["Arroz Costeño 750 g"])
    descripcion: str | None = Field(default=None, max_length=500, examples=["Arroz extra, bolsa de 750 g"])
    imagen_url: str | None = Field(default=None, max_length=500, pattern=_PATRON_IMAGEN, examples=["https://ejemplo.pe/img/arroz.jpg"])
    unidad_id: int = Field(gt=0, description="Ver GET /unidades-medida", examples=[1])
    marca_id: int | None = Field(default=None, gt=0, description="Opcional; no aplica a servicios")
    proveedor_id: int | None = Field(default=None, gt=0, description="Opcional")
    precio_contado: Decimal = _precio(description="Precio si se paga al contado", examples=["4.20"])
    precio_lista: Decimal = _precio(description="Precio a crédito (precio de lista); no puede ser menor al de contado", examples=["4.60"])
    permite_fin_de_mes: bool = Field(default=True, description="Se puede pagar en un solo pago a fin de mes")
    permite_cuotas: bool = Field(default=False, description="Se puede pagar en cuotas (método francés)")

    @model_validator(mode="after")
    def _reglas(self):
        if self.precio_lista < self.precio_contado:
            raise ValueError("El precio de lista (a crédito) no puede ser menor que el precio de contado")
        if not (self.permite_fin_de_mes or self.permite_cuotas):
            raise ValueError("El producto debe poder venderse a fin de mes, en cuotas, o en ambas formas")
        return self


class ProductoActualizar(_Base):
    """Cambio parcial: solo se modifican los campos que se envían."""

    codigo: str | None = Field(default=None, pattern=_PATRON_CODIGO)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = Field(default=None, max_length=500)
    imagen_url: str | None = Field(default=None, max_length=500, pattern=_PATRON_IMAGEN)
    unidad_id: int | None = Field(default=None, gt=0)
    marca_id: int | None = Field(default=None, gt=0)
    proveedor_id: int | None = Field(default=None, gt=0)
    precio_contado: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    precio_lista: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    permite_fin_de_mes: bool | None = None
    permite_cuotas: bool | None = None


class UnidadResumen(BaseModel):
    id_unidad: int
    codigo: str
    nombre: str


class MarcaResumen(BaseModel):
    id_marca: int
    nombre: str


class ProveedorResumen(BaseModel):
    id_proveedor: int
    razon_social: str


class ProductoRespuesta(BaseModel):
    id_producto: int
    codigo: str
    nombre: str
    descripcion: str | None
    imagen_url: str | None
    unidad: UnidadResumen
    marca: MarcaResumen | None
    proveedor: ProveedorResumen | None
    precio_contado: Decimal
    precio_lista: Decimal
    permite_fin_de_mes: bool
    permite_cuotas: bool
    activo: bool

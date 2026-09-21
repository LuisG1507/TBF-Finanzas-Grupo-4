import enum


class RolCodigo(str, enum.Enum):
    ADMIN_SIS = "ADMIN_SIS"
    ADMIN_NEG = "ADMIN_NEG"
    CLIENTE = "CLIENTE"


class TipoTasa(str, enum.Enum):
    NOMINAL = "NOMINAL"
    EFECTIVA = "EFECTIVA"


class ModalidadCompra(str, enum.Enum):
    FIN_DE_MES = "FIN_DE_MES"
    CUOTAS = "CUOTAS"


class EstadoCompra(str, enum.Enum):
    VIGENTE = "VIGENTE"
    CANCELADA = "CANCELADA"
    ANULADA = "ANULADA"


class EstadoCuota(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    FACTURADA = "FACTURADA"
    PAGADA = "PAGADA"
    VENCIDA = "VENCIDA"


class EstadoCuentaEstado(str, enum.Enum):
    EMITIDO = "EMITIDO"
    PAGADO = "PAGADO"
    VENCIDO = "VENCIDO"


class TipoItemEstadoCuenta(str, enum.Enum):
    COMPRA = "COMPRA"
    CUOTA = "CUOTA"
    INT_COMPENSATORIO = "INT_COMPENSATORIO"
    INT_MORATORIO = "INT_MORATORIO"


class EstadoPago(str, enum.Enum):
    REGISTRADO = "REGISTRADO"
    ANULADO = "ANULADO"


class AccionBitacora(str, enum.Enum):
    ALTA = "ALTA"
    BAJA = "BAJA"
    MODIFICACION = "MODIFICACION"
    ANULACION = "ANULACION"


class EntidadBitacora(str, enum.Enum):
    TIENDA = "TIENDA"
    PRODUCTO = "PRODUCTO"
    CLIENTE = "CLIENTE"
    USUARIO = "USUARIO"
    COMPRA = "COMPRA"
    PAGO = "PAGO"
    ESTADO_CUENTA = "ESTADO_CUENTA"

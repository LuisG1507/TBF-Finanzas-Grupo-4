// Reflejan 1 a 1 los enums y modelos de app/models/*.py del backend (Backend-Grupo4).

export type RolCodigo = 'ADMIN_SIS' | 'ADMIN_NEG' | 'CLIENTE'

export type TipoTasa = 'NOMINAL' | 'EFECTIVA'

export type ModalidadCompra = 'FIN_DE_MES' | 'CUOTAS'

export type EstadoCompra = 'VIGENTE' | 'CANCELADA' | 'ANULADA'

export type EstadoCuota = 'PENDIENTE' | 'FACTURADA' | 'PAGADA' | 'VENCIDA'

export type EstadoCuentaEstado = 'EMITIDO' | 'PAGADO' | 'VENCIDO'

export type TipoItemEstadoCuenta = 'COMPRA' | 'CUOTA' | 'INT_COMPENSATORIO' | 'INT_MORATORIO'

export type MonedaCodigo = 'PEN' | 'USD'

export interface Moneda {
  codigo_iso: MonedaCodigo
  simbolo: string
}

export interface Tienda {
  id_tienda: number
  ruc: string
  razon_social: string
  nombre_comercial: string
  giro: string
  direccion: string | null
  telefono: string | null
  email: string | null
  activo: boolean
}

export interface Proveedor {
  id_proveedor: number
  razon_social: string
  activo: boolean
}

export interface Marca {
  id_marca: number
  nombre: string
  activo: boolean
}

export interface UnidadMedida {
  id_unidad: number
  codigo: string
  nombre: string
}

export interface Producto {
  id_producto: number
  codigo: string
  nombre: string
  descripcion: string | null
  imagen_url: string | null
  proveedor: Pick<Proveedor, 'id_proveedor' | 'razon_social'> | null
  marca: Pick<Marca, 'id_marca' | 'nombre'> | null
  unidad: UnidadMedida
  precio_contado: string
  precio_lista: string
  permite_fin_de_mes: boolean
  permite_cuotas: boolean
  activo: boolean
}

export interface TasaPactada {
  tipo: TipoTasa
  tasa_pct: string
  plazo_dias: number
  capitalizacion_dias: number | null
}

export interface CondicionCredito {
  id_condicion: number
  moneda: Moneda
  tasa_compensatoria: TasaPactada
  tasa_moratoria: TasaPactada
  limite_credito: string
  max_meses: number
  dia_corte: number
  hora_corte: string
  dia_pago: number
  vigente_desde: string
  vigente_hasta: string | null
}

export interface Cliente {
  id_cliente: number
  tipo_documento: string
  numero_documento: string
  nombres: string
  apellidos: string
  telefono: string | null
  direccion: string | null
  email: string | null
  usuario: string
  activo: boolean
  condicion: CondicionCredito | null
}

export interface CreditoDisponible {
  moneda: Moneda
  limite_credito: string
  capital_pendiente: string
  credito_disponible: string
}

export interface DetalleCompra {
  producto_id: number
  codigo: string
  nombre: string
  cantidad: string
  precio_unitario: string
  subtotal: string
}

export interface Compra {
  id_compra: number | null
  cliente: { id_cliente: number; nombre: string; documento: string }
  fecha_hora_compra: string
  modalidad: ModalidadCompra
  moneda: Moneda
  num_cuotas: number
  monto_total: string
  fecha_corte: string
  fecha_primer_pago: string
  dias_gracia: number
  capital_capitalizado: string
  interes_gracia: string
  tep_aplicada: string
  cuota: string | null
  total_intereses: string
  total_a_pagar: string
  tcea_pct: string | null
  estado: EstadoCompra | null
  items: DetalleCompra[]
  cronograma: Cuota[]
  credito: Omit<CreditoDisponible, 'moneda'> & { excede_limite: boolean } | null
}

export interface Cuota {
  numero: number
  fecha_vencimiento: string
  saldo_inicial: string
  interes: string
  amortizacion: string
  monto_cuota: string
  saldo_final: string
  estado: EstadoCuota
}

export interface EstadoCuentaDetalle {
  id_detalle_ec: number
  tipo_item: TipoItemEstadoCuenta
  concepto: string
  fecha_referencia: string | null
  fecha_hora_compra: string | null
  dias_transcurridos: number | null
  tasa_aplicada: string | null
  monto: string
  orden: number
}

export interface EstadoCuenta {
  id_estado_cuenta: number
  cliente_id: number
  cliente_nombre: string
  moneda: Moneda | null
  anio: number
  mes: number
  fecha_corte: string
  fecha_pago: string
  total_capital: string
  total_interes_comp: string
  total_interes_mora: string
  total_pagar: string
  estado: EstadoCuentaEstado
}

export interface EstadoCuentaCompleto extends EstadoCuenta {
  detalles: EstadoCuentaDetalle[]
}

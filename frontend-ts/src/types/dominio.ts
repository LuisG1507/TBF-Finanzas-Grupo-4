// Reflejan 1 a 1 los enums y modelos de app/models/*.py del backend (Backend-Grupo4).

export type RolCodigo = 'ADMIN_SIS' | 'ADMIN_NEG' | 'CLIENTE'

export type TipoTasa = 'NOMINAL' | 'EFECTIVA'

export type ModalidadCompra = 'FIN_DE_MES' | 'CUOTAS'

export type EstadoCompra = 'VIGENTE' | 'CANCELADA' | 'ANULADA'

export type EstadoCuota = 'PENDIENTE' | 'FACTURADA' | 'PAGADA' | 'VENCIDA'

export type EstadoCuentaEstado = 'EMITIDO' | 'PAGADO' | 'VENCIDO'

export type TipoItemEstadoCuenta = 'COMPRA' | 'CUOTA' | 'INT_COMPENSATORIO' | 'INT_MORATORIO'

export type EstadoPago = 'REGISTRADO' | 'ANULADO'

export interface Tienda {
  id_tienda: number
  ruc: string
  razon_social: string
  nombre_comercial: string
  giro: string
  direccion?: string
  telefono?: string
  email?: string
  activo: boolean
}

export interface Usuario {
  id_usuario: number
  username: string
  rol: RolCodigo
  tienda_id?: number
  activo: boolean
}

export interface Proveedor {
  id_proveedor: number
  razon_social: string
}

export interface Marca {
  id_marca: number
  nombre: string
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
  descripcion?: string
  proveedor_id?: number
  marca_id?: number
  unidad_id: number
  imagen_url?: string
  precio_contado: string
  precio_lista: string
  permite_fin_de_mes: boolean
  permite_cuotas: boolean
  activo: boolean
}

export interface CondicionCredito {
  id_condicion: number
  cliente_id: number
  moneda_codigo: 'PEN'
  tasa_compensatoria: string
  tipo_tasa_comp: TipoTasa
  plazo_tasa_comp_dias: number
  capitaliz_comp_dias?: number
  tasa_moratoria: string
  tipo_tasa_mora: TipoTasa
  plazo_tasa_mora_dias: number
  capitaliz_mora_dias?: number
  limite_credito: string
  max_meses: number
  dia_corte: number
  hora_corte: string
  dia_pago: number
}

export interface Cliente {
  id_cliente: number
  tipo_documento: string
  numero_documento: string
  nombres: string
  apellidos: string
  telefono?: string
  email?: string
  activo: boolean
  condicion: CondicionCredito
}

export interface DetalleCompra {
  id_detalle: number
  producto_id: number
  cantidad: string
  precio_unitario: string
  subtotal: string
}

export interface Compra {
  id_compra: number
  cliente_id: number
  fecha_hora_compra: string
  modalidad: ModalidadCompra
  num_cuotas: number
  monto_total: string
  fecha_corte_asignada: string
  fecha_primer_pago: string
  dias_gracia: number
  capital_capitalizado: string
  estado: EstadoCompra
  detalles: DetalleCompra[]
}

export interface Cuota {
  id_cuota: number
  compra_id: number
  numero_cuota: number
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
  fecha_referencia?: string
  dias_transcurridos?: number
  tasa_aplicada?: string
  monto: string
  orden: number
}

export interface EstadoCuenta {
  id_estado_cuenta: number
  cliente_id: number
  anio: number
  mes: number
  fecha_corte: string
  fecha_pago: string
  total_capital: string
  total_interes_comp: string
  total_interes_mora: string
  total_pagar: string
  estado: EstadoCuentaEstado
  detalles: EstadoCuentaDetalle[]
}

export interface Pago {
  id_pago: number
  cliente_id: number
  fecha_hora_pago: string
  monto_pagado: string
  monto_mora_aplicado: string
  monto_interes_comp_aplicado: string
  monto_capital_aplicado: string
  estado: EstadoPago
}

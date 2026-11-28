// Cómo se muestra cada valor de los enums del backend: el texto y el color del chip.

import type { TonoInsignia } from '../components/ui/Insignia'
import type { EstadoCompra, EstadoCuentaEstado, EstadoCuota, TipoItemEstadoCuenta, TipoTasa } from '../types/dominio'
import type { SituacionCliente } from '../types/resumen'

interface Presentacion {
  texto: string
  tono: TonoInsignia
}

export const SITUACION_CLIENTE: Record<SituacionCliente, Presentacion> = {
  AL_DIA: { texto: 'Al día', tono: 'exito' },
  POR_VENCER: { texto: 'Por vencer', tono: 'alerta' },
  EN_MORA: { texto: 'En mora', tono: 'peligro' },
}

export const ESTADO_CUENTA: Record<EstadoCuentaEstado, Presentacion> = {
  EMITIDO: { texto: 'Emitido', tono: 'neutro' },
  PAGADO: { texto: 'Pagado', tono: 'exito' },
  VENCIDO: { texto: 'Vencido', tono: 'peligro' },
}

export const ESTADO_COMPRA: Record<EstadoCompra, Presentacion> = {
  VIGENTE: { texto: 'Por pagar', tono: 'neutro' },
  CANCELADA: { texto: 'Pagada', tono: 'exito' },
  ANULADA: { texto: 'Anulada', tono: 'peligro' },
}

export const ESTADO_CUOTA: Record<EstadoCuota, Presentacion> = {
  PENDIENTE: { texto: 'Pendiente', tono: 'neutro' },
  FACTURADA: { texto: 'Facturada', tono: 'alerta' },
  PAGADA: { texto: 'Pagada', tono: 'exito' },
  VENCIDA: { texto: 'Vencida', tono: 'peligro' },
}

export const TIPO_ITEM: Record<TipoItemEstadoCuenta, string> = {
  COMPRA: 'Compra',
  CUOTA: 'Cuota',
  INT_COMPENSATORIO: 'Interés compensatorio',
  INT_MORATORIO: 'Interés moratorio',
}

export const TIPO_TASA: Record<TipoTasa, string> = {
  NOMINAL: 'Nominal',
  EFECTIVA: 'Efectiva',
}

/** "anual", "mensual"… o "a 45 días" si el plazo no es uno de los habituales. */
export function nombreDelPlazo(dias: number): string {
  const habituales: Record<number, string> = {
    1: 'diaria',
    15: 'quincenal',
    30: 'mensual',
    60: 'bimestral',
    90: 'trimestral',
    120: 'cuatrimestral',
    180: 'semestral',
    360: 'anual',
  }
  return habituales[dias] ?? `a ${dias} días`
}

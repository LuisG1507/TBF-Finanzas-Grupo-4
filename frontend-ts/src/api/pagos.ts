import type { CondicionCredito, EstadoCuenta } from '../types/dominio'
import { llamarFinanzas } from './finanzas'

/** Lo que responde POST /api/v1/finanzas/pagos (los importes llegan como texto decimal). */
export interface RespuestaPago {
  dias_mora: number
  tasa_mora_pct: string
  interes_mora: string
  total_exigible: string
  aceptado: boolean
  motivo: string | null
  monto_aplicado: string
  aplicado_mora: string
  aplicado_interes_comp: string
  aplicado_capital: string
  aplicado_portes: string
  aplicado_seguro: string
  excedente_devuelto: string
}

export const SIN_CONEXION = 'No se pudo conectar con el backend. Inicia «uvicorn app.main:app --reload» y vuelve a intentarlo.'

/**
 * Envía al backend el pago de un estado de cuenta. El backend calcula los días de mora (30/360),
 * el interés moratorio con la tasa pactada del cliente, rechaza el pago si no cubre el total
 * y, si lo cubre, lo reparte en mora, interés compensatorio y capital y devuelve el excedente.
 */
export async function procesarPago(
  estadoCuenta: EstadoCuenta,
  condicion: CondicionCredito,
  fechaPago: string,
  montoPagado: string,
): Promise<RespuestaPago> {
  const { ok, datos } = await llamarFinanzas('pagos', {
    capital_exigible: estadoCuenta.total_capital,
    interes_comp_exigible: estadoCuenta.total_interes_comp,
    fecha_vencimiento: estadoCuenta.fecha_pago,
    fecha_pago: fechaPago,
    monto_pagado: montoPagado,
    tipo_tasa_mora: condicion.tipo_tasa_mora,
    tasa_mora_pct: Number(condicion.tasa_moratoria).toFixed(4),
    plazo_tasa_mora: condicion.plazo_tasa_mora_dias,
    capitalizacion_mora: condicion.tipo_tasa_mora === 'NOMINAL' ? condicion.capitaliz_mora_dias : null,
  })
  if (!ok || datos === null) throw new Error(SIN_CONEXION)
  return datos as RespuestaPago
}

/** Total exigible a una fecha, sin registrar nada: se consulta con un monto simbólico. */
export function consultarExigible(estadoCuenta: EstadoCuenta, condicion: CondicionCredito, fechaPago: string) {
  return procesarPago(estadoCuenta, condicion, fechaPago, '0.01')
}

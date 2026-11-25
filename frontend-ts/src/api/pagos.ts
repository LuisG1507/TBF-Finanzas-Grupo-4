import { pedir } from './cliente'

export interface RespuestaExigible {
  dias_mora: number
  tasa_mora_pct: string
  capital: string
  interes_comp: string
  interes_mora: string
  interes_comp_atraso: string
  total_exigible: string
}

export interface RespuestaPago extends RespuestaExigible {
  id_pago: number
  aplicado_mora: string
  aplicado_interes_comp: string
  aplicado_capital: string
  excedente_devuelto: string
}

const RUTA = '/pagos/estados-cuenta'

export function rutaExigible(estadoId: number, fechaPago: string) {
  return RUTA + '/' + estadoId + '/exigible?fecha_pago=' + encodeURIComponent(fechaPago)
}

export function registrarPago(estadoId: number, fechaPago: string, monto: string) {
  return pedir<RespuestaPago>(RUTA + '/' + estadoId, {
    method: 'POST', cuerpo: { fecha_pago: fechaPago, monto_pagado: monto },
  })
}

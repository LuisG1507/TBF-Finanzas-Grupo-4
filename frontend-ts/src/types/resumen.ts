// Datos de resumen que alimentan el tablero del administrador del negocio.
// Importes decimales devueltos por el backend.

import type { CondicionCredito, EstadoCuota, MonedaCodigo } from './dominio'

export type SituacionCliente = 'AL_DIA' | 'POR_VENCER' | 'EN_MORA'

/** Cómo está hoy la cuenta de un cliente. */
export interface PosicionCliente {
  cliente_id: number
  moneda: MonedaCodigo
  /** Capital pendiente: es lo que se compara contra el límite de crédito. */
  saldo_capital: string
  saldo_capital_pen: string
  mora_acumulada: string
  /** Días de atraso del pago vencido más antiguo (conteo comercial 30/360). 0 si está al día. */
  dias_atraso: number
  situacion: SituacionCliente
  /** Fecha del pago pendiente más próximo (o del vencido más antiguo, si está en mora). */
  proximo_vencimiento: string | null
  monto_proximo_pago: string | null
  /** Saldo de capital al cierre de los meses anteriores (del más antiguo al más reciente). */
  saldos_cierre_previos: string[]
  saldos_cierre_previos_pen: string[]
}

export interface CobranzaSemanal {
  desde: string
  hasta: string
  /** Lo que vencía en la semana. */
  programado: string
  /** Lo que efectivamente se cobró. */
  cobrado: string
}

export interface CuotaDelMes {
  cliente_id: number
  fecha_vencimiento: string
  monto: string
  estado: EstadoCuota
}

/** Cierre de un mes anterior, para las tendencias de los indicadores. */
export interface CierreMensual {
  /** Primer día del mes, en formato AAAA-MM-DD. */
  mes: string
  cuotas_programadas: string
  mora_acumulada: string
  clientes_activos: number
}

export interface RespuestaTablero {
  hoy: string
  moneda_base: 'PEN'
  kpis: { saldo_por_cobrar: string; cuotas_del_mes: string; mora_acumulada: string; clientes_activos: number }
  posiciones: PosicionCliente[]
  cobranza_semanal: CobranzaSemanal[]
  cuotas_del_mes: CuotaDelMes[]
  cierres_mensuales: CierreMensual[]
}

export interface ResumenMiCuenta {
  hoy: string
  tienda: string
  posicion: PosicionCliente
  condicion: CondicionCredito | null
  credito_disponible: string | null
}

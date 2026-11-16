const LOCAL = 'es-PE'

/*
  Las fechas del backend llegan como texto ISO. Una fecha sola ("2026-11-26") no lleva hora, y
  `new Date("2026-11-26")` la interpreta como medianoche UTC: en Perú (UTC−5) eso es el día 25 a las 7 p. m.
  Por eso las fechas sin hora se construyen a mano, en hora local.
*/
function aFecha(iso: string): Date {
  const soloFecha = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  if (soloFecha) return new Date(Number(soloFecha[1]), Number(soloFecha[2]) - 1, Number(soloFecha[3]))
  return new Date(iso)
}

/** "15 nov." → "15 nov": el punto de la abreviatura estorba en tablas y gráficos. */
function sinPuntoDeAbreviatura(texto: string): string {
  return texto.replace(/\./g, '')
}

export function formatearSoles(valor: string | number): string {
  const numero = typeof valor === 'string' ? Number(valor) : valor
  return `S/ ${numero.toLocaleString(LOCAL, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

/** Soles sin céntimos, para los ejes de los gráficos: "S/ 800". */
export function formatearSolesEntero(valor: number): string {
  return `S/ ${valor.toLocaleString(LOCAL, { maximumFractionDigits: 0 })}`
}

/** "26 nov 2026" */
export function formatearFecha(iso: string): string {
  return sinPuntoDeAbreviatura(aFecha(iso).toLocaleDateString(LOCAL, { day: 'numeric', month: 'short', year: 'numeric' }))
}

/** "26 nov" */
export function formatearFechaCorta(iso: string): string {
  return sinPuntoDeAbreviatura(aFecha(iso).toLocaleDateString(LOCAL, { day: 'numeric', month: 'short' }))
}

/** "15 de noviembre de 2026" */
export function formatearFechaLarga(iso: string): string {
  return aFecha(iso).toLocaleDateString(LOCAL, { day: 'numeric', month: 'long', year: 'numeric' })
}

/** "15 sep 2026, 6:30 p. m." */
export function formatearFechaHora(iso: string): string {
  const fecha = aFecha(iso)
  const hora = fecha.toLocaleTimeString(LOCAL, { hour: 'numeric', minute: '2-digit' })
  return `${formatearFecha(iso)}, ${hora}`
}

/** Nombre del mes en minúscula, como se escribe en español: "noviembre" (o "nov" con abreviado = true). */
export function nombreDelMes(iso: string, abreviado = false): string {
  const nombre = aFecha(iso).toLocaleDateString(LOCAL, { month: abreviado ? 'short' : 'long' })
  return sinPuntoDeAbreviatura(nombre).toLowerCase()
}

/** "Del 9 al 15 nov" o "Del 28 sep al 4 oct" si la semana cruza de mes. */
export function formatearRango(desdeIso: string, hastaIso: string): string {
  const desde = aFecha(desdeIso)
  const hasta = aFecha(hastaIso)
  const mismoMes = desde.getMonth() === hasta.getMonth() && desde.getFullYear() === hasta.getFullYear()
  const inicio = mismoMes ? String(desde.getDate()) : formatearFechaCorta(desdeIso)
  return `Del ${inicio} al ${formatearFechaCorta(hastaIso)}`
}

/** Las tasas se muestran siempre con 7 decimales (Anexo A del curso): "24.0000000 %". */
export function formatearTasa(valor: string): string {
  return `${Number(valor).toFixed(7)} %`
}

/** Fracción a porcentaje: 0.8217 → "82 %". */
export function formatearPorcentaje(fraccion: number, decimales = 0): string {
  return `${(fraccion * 100).toLocaleString(LOCAL, { minimumFractionDigits: decimales, maximumFractionDigits: decimales })} %`
}

/** Variación con signo: 0.046 → "+4.6 %", −0.158 → "−15.8 %". */
export function formatearVariacion(fraccion: number, decimales = 1): string {
  const signo = fraccion > 0 ? '+' : fraccion < 0 ? '−' : ''
  return `${signo}${formatearPorcentaje(Math.abs(fraccion), decimales)}`
}

/** "1 cliente" / "3 clientes" */
export function plural(cantidad: number, singular: string, pluralDe: string): string {
  return `${cantidad} ${cantidad === 1 ? singular : pluralDe}`
}

/*
  Sumar montos en la interfaz. Los montos llegan como texto ("349.28") porque el backend usa Decimal;
  para no arrastrar errores de punto flotante se suman en céntimos enteros.
  Solo se usa para totales de pantalla: los cálculos financieros los hace siempre el backend.
*/
export function sumarMontos(montos: (string | number)[]): number {
  const centimos = montos.reduce<number>((suma, monto) => suma + Math.round(Number(monto) * 100), 0)
  return centimos / 100
}

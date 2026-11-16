import { useState } from 'react'
import styles from './BarraSegmentada.module.css'

export interface Segmento {
  clave: string
  etiqueta: string
  /** Dato secundario junto al nombre, por ejemplo "5 clientes". */
  detalle?: string
  valor: number
  /** El valor ya formateado, por ejemplo "S/ 3,140.30". */
  textoValor: string
  /** Color de estado: de "bien" (verde) a "critico" (rojo). */
  tono: 'bien' | 'aviso' | 'serio' | 'critico'
}

interface BarraSegmentadaProps {
  segmentos: Segmento[]
  /** Qué representa el total, para los lectores de pantalla. */
  descripcion: string
  formatearPorcentaje: (fraccion: number) => string
}

/*
  Un total repartido en partes: una barra fina arriba y, debajo, la lista con el nombre,
  el monto y la participación de cada parte. La barra no lleva texto porque la lista ya da las cifras,
  y cada fila repite el color con una muestra, así que el color nunca es el único indicio.
*/
export function BarraSegmentada({ segmentos, descripcion, formatearPorcentaje }: BarraSegmentadaProps) {
  const [resaltado, setResaltado] = useState<string | null>(null)
  const total = segmentos.reduce((suma, segmento) => suma + segmento.valor, 0)
  const fraccion = (valor: number) => (total > 0 ? valor / total : 0)

  const resumen = segmentos
    .map((segmento) => `${segmento.etiqueta}: ${segmento.textoValor} (${formatearPorcentaje(fraccion(segmento.valor))})`)
    .join('; ')

  return (
    <div className={styles.contenedor}>
      <div className={styles.barra} role="img" aria-label={`${descripcion} ${resumen}.`}>
        {segmentos
          .filter((segmento) => segmento.valor > 0)
          .map((segmento) => (
            <span
              key={segmento.clave}
              className={[styles.segmento, styles[segmento.tono], resaltado && resaltado !== segmento.clave && styles.atenuado]
                .filter(Boolean)
                .join(' ')}
              style={{ flexGrow: segmento.valor }}
              title={`${segmento.etiqueta}: ${segmento.textoValor}`}
              onPointerEnter={() => setResaltado(segmento.clave)}
              onPointerLeave={() => setResaltado(null)}
            />
          ))}
      </div>

      <ul className={styles.lista}>
        {segmentos.map((segmento) => (
          <li
            key={segmento.clave}
            className={[styles.fila, resaltado && resaltado !== segmento.clave && styles.filaAtenuada].filter(Boolean).join(' ')}
            onPointerEnter={() => setResaltado(segmento.clave)}
            onPointerLeave={() => setResaltado(null)}
          >
            <span className={[styles.muestra, styles[segmento.tono]].join(' ')} aria-hidden="true" />
            <span className={styles.nombre}>
              {segmento.etiqueta}
              {segmento.detalle && <span className={styles.detalle}>{segmento.detalle}</span>}
            </span>
            <span className={styles.valor}>{segmento.textoValor}</span>
            <span className={styles.porcentaje}>{formatearPorcentaje(fraccion(segmento.valor))}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

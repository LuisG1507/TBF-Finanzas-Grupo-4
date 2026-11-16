import styles from './MiniTendencia.module.css'

interface MiniTendenciaProps {
  valores: number[]
  /** Resumen de la tendencia para los lectores de pantalla y el tooltip. */
  descripcion: string
}

const ANCHO = 88
const ALTO = 28
const MARGEN = 4

/** Línea de tendencia en miniatura para las filas de una tabla. El punto marca el valor actual. */
export function MiniTendencia({ valores, descripcion }: MiniTendenciaProps) {
  if (valores.length < 2) return null

  const minimo = Math.min(...valores)
  const maximo = Math.max(...valores)
  const rango = maximo - minimo
  const paso = (ANCHO - 2 * MARGEN) / (valores.length - 1)

  const puntos = valores.map((valor, indice) => {
    const proporcion = rango > 0 ? (valor - minimo) / rango : 0.5
    return [MARGEN + paso * indice, ALTO - MARGEN - proporcion * (ALTO - 2 * MARGEN)] as const
  })
  const [xFinal, yFinal] = puntos[puntos.length - 1]

  return (
    <svg
      className={styles.miniTendencia}
      width={ANCHO}
      height={ALTO}
      viewBox={`0 0 ${ANCHO} ${ALTO}`}
      role="img"
      aria-label={descripcion}
    >
      <title>{descripcion}</title>
      <polyline className={styles.linea} points={puntos.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')} />
      <circle className={styles.punto} cx={xFinal} cy={yFinal} r={3.5} />
    </svg>
  )
}

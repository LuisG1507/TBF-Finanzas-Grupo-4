import styles from './MiniBarras.module.css'

interface MiniBarrasProps {
  valores: number[]
  /** Texto de cada barra al pasar el cursor, en el mismo orden que los valores. */
  etiquetas: string[]
  /** Resumen de la tendencia para los lectores de pantalla. */
  descripcion: string
  /** Para usarlas sobre la tarjeta destacada (verde oscuro). */
  sobreOscuro?: boolean
}

// La barra más baja conserva algo de altura para que siempre se vea.
const ALTURA_MINIMA = 0.2

/*
  Mini-barras de tendencia para las tarjetas de indicadores.
  Muestran la forma de la tendencia, no cantidades exactas: la altura va del valor más bajo
  al más alto de la serie. El último período (el actual) va en el color de acento.
*/
export function MiniBarras({ valores, etiquetas, descripcion, sobreOscuro }: MiniBarrasProps) {
  if (valores.length === 0) return null

  const minimo = Math.min(...valores)
  const maximo = Math.max(...valores)
  const rango = maximo - minimo

  return (
    <div className={[styles.miniBarras, sobreOscuro && styles.sobreOscuro].filter(Boolean).join(' ')} role="img" aria-label={descripcion}>
      {valores.map((valor, indice) => {
        const proporcion = rango > 0 ? (valor - minimo) / rango : 0.5
        const altura = ALTURA_MINIMA + (1 - ALTURA_MINIMA) * proporcion
        const esActual = indice === valores.length - 1
        return (
          <span
            key={indice}
            className={[styles.barra, esActual && styles.actual].filter(Boolean).join(' ')}
            style={{ height: `${altura * 100}%` }}
            title={etiquetas[indice]}
          />
        )
      })}
    </div>
  )
}

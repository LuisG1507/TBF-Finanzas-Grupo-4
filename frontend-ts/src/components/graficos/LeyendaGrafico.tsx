import styles from './LeyendaGrafico.module.css'

interface ElementoLeyenda {
  etiqueta: string
  /** barra: la serie principal · pista: la referencia de fondo */
  muestra: 'barra' | 'pista'
}

/** Leyenda de un gráfico: una muestra de color junto al nombre de cada serie. */
export function LeyendaGrafico({ elementos }: { elementos: ElementoLeyenda[] }) {
  return (
    <ul className={styles.leyenda}>
      {elementos.map((elemento) => (
        <li key={elemento.etiqueta} className={styles.elemento}>
          <span className={[styles.muestra, styles[elemento.muestra]].join(' ')} aria-hidden="true" />
          {elemento.etiqueta}
        </li>
      ))}
    </ul>
  )
}

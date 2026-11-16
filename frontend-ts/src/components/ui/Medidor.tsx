import styles from './Medidor.module.css'

interface MedidorProps {
  /** Nombre de lo que se mide, para los lectores de pantalla. */
  etiqueta: string
  valor: number
  maximo: number
  /** Cómo leer el valor en voz alta, por ejemplo "S/ 678.15 de S/ 1,500.00". */
  textoValor: string
  tono?: 'acento' | 'alerta' | 'peligro'
  /** Para usarlo dentro de una tarjeta verde claro. */
  sobreSuave?: boolean
}

/** Una proporción contra un límite. La pista es un paso más claro del mismo color que el relleno. */
export function Medidor({ etiqueta, valor, maximo, textoValor, tono = 'acento', sobreSuave }: MedidorProps) {
  const proporcion = maximo > 0 ? Math.min(Math.max(valor / maximo, 0), 1) : 0
  return (
    <div
      className={[styles.pista, styles[tono], sobreSuave && styles.sobreSuave].filter(Boolean).join(' ')}
      role="meter"
      aria-label={etiqueta}
      aria-valuemin={0}
      aria-valuemax={maximo}
      aria-valuenow={Math.min(Math.max(valor, 0), maximo)}
      aria-valuetext={textoValor}
    >
      <div className={styles.relleno} style={{ width: `${proporcion * 100}%` }} />
    </div>
  )
}

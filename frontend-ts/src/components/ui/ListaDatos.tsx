import type { ReactNode } from 'react'
import styles from './ListaDatos.module.css'

/** Lista de pares etiqueta → valor (el desglose de un pago, el resumen de un crédito). */
export function ListaDatos({ children }: { children: ReactNode }) {
  return <dl className={styles.lista}>{children}</dl>
}

interface FilaDatoProps {
  etiqueta: string
  valor: ReactNode
  /** Fila de total: más grande y en negrita. */
  enfasis?: boolean
  tono?: 'peligro'
  /** Línea fina encima, para separar el total del resto. */
  separada?: boolean
}

export function FilaDato({ etiqueta, valor, enfasis, tono, separada }: FilaDatoProps) {
  const clases = [styles.fila, enfasis && styles.enfasis, tono === 'peligro' && styles.peligro, separada && styles.separada]
    .filter(Boolean)
    .join(' ')
  return (
    <div className={clases}>
      <dt>{etiqueta}</dt>
      <dd>{valor}</dd>
    </div>
  )
}

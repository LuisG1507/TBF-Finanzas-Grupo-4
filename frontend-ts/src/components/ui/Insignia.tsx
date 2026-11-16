import styles from './Insignia.module.css'

export type TonoInsignia = 'neutro' | 'exito' | 'alerta' | 'peligro'

interface InsigniaProps {
  texto: string
  tono?: TonoInsignia
  /** Punto de color a la izquierda. Por defecto lo llevan los estados (éxito, alerta, peligro). */
  punto?: boolean
}

/** Chip de estado. El color nunca va solo: siempre lo acompaña el texto. */
export function Insignia({ texto, tono = 'neutro', punto = tono !== 'neutro' }: InsigniaProps) {
  return (
    <span className={[styles.insignia, styles[tono]].join(' ')}>
      {punto && <span className={styles.punto} aria-hidden="true" />}
      {texto}
    </span>
  )
}
